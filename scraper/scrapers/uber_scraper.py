"""
Uber Scraper — API approach
────────────────────────────
Calls Uber's internal price estimate API directly (no browser UI needed).
Much more reliable than DOM scraping.

Uber exposes a public-ish REST endpoint used by their web price estimator:
  GET https://www.uber.com/api/v1/marketplace/product-estimates
  with start/end lat+lng as query params.

Falls back to a full-page Playwright scrape if the API fails.
"""

import asyncio
import re
import httpx
from typing import List, Dict, Optional

from playwright.async_api import Page, Response

from scrapers.base import BaseScraper, build_record, detect_surge
from config import SCRAPER


# Uber product names we care about (maps internal name → display name)
UBER_PRODUCTS = {
    "ubergo":       "UberGo",
    "ubermoto":     "Uber Moto",
    "uberauto":     "Uber Auto",
    "uberx":        "UberX",
    "uberxl":       "UberXL",
    "ubergo sedan": "UberGo Sedan",
    "premier":      "Premier",
    "comfort":      "Comfort",
}


class UberScraper(BaseScraper):
    platform_key = "uber"
    platform_name = "Uber"

    # Uber's price estimate API endpoint
    ESTIMATE_URL = "https://www.uber.com/api/v1/marketplace/product-estimates"

    # Fallback: price estimate page
    WEB_URL = "https://www.uber.com/in/en/price-estimate/"

    async def scrape_od(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        # Try API approach first
        records = await self._api_scrape(od, run_id)
        if records:
            self.logger.info("[Uber] API: %s → %d records", od["label"], len(records))
            return records

        # Fallback: intercept network calls from the web page
        self.logger.info("[Uber] API failed, trying network interception for %s", od["label"])
        records = await self._intercept_scrape(page, od, run_id)
        if records:
            return records

        # Last resort: text parsing
        self.logger.warning("[Uber] Both approaches failed for %s", od["label"])
        return [build_record(
            platform=self.platform_key, od=od, service_name="ALL",
            price_raw=None, run_id=run_id, status="failed",
            error_msg="Could not extract fares via API or interception",
        )]

    async def _api_scrape(self, od: Dict, run_id: str) -> List[Dict]:
        """Call Uber's price estimate API directly."""
        params = {
            "start_latitude":  od["origin"]["lat"],
            "start_longitude": od["origin"]["lng"],
            "end_latitude":    od["destination"]["lat"],
            "end_longitude":   od["destination"]["lng"],
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.uber.com/in/en/price-estimate/",
            "x-csrf-token": "x",
        }

        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(self.ESTIMATE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    self.logger.debug("[Uber] API returned %d", resp.status_code)
                    return []
                data = resp.json()
        except Exception as e:
            self.logger.debug("[Uber] API request failed: %s", e)
            return []

        return self._parse_api_response(data, od, run_id)

    def _parse_api_response(self, data: dict, od: Dict, run_id: str) -> List[Dict]:
        records = []
        # Uber's response shape varies — try multiple paths
        products = (
            data.get("products") or
            data.get("data", {}).get("products") or
            data.get("prices") or
            data.get("data", {}).get("prices") or
            []
        )

        if not products:
            return []

        for p in products:
            name = (
                p.get("display_name") or
                p.get("name") or
                p.get("localized_display_name", "Unknown")
            )
            # Price range
            low  = p.get("low_estimate") or p.get("estimate") or p.get("price_details", {}).get("minimum")
            high = p.get("high_estimate") or p.get("price_details", {}).get("base")
            currency_code = p.get("currency_code", "INR")

            if low:
                price_raw = f"₹{int(low)}" + (f" - ₹{int(high)}" if high and high != low else "")
            else:
                price_raw = p.get("estimate")  # sometimes a string like "₹120-₹150"

            eta = p.get("estimate") if isinstance(p.get("estimate"), int) else None
            surge = p.get("surge_multiplier", 1.0)

            records.append(build_record(
                platform=self.platform_key,
                od=od,
                service_name=name,
                price_raw=price_raw,
                run_id=run_id,
                eta_minutes=p.get("duration"),
                surge={"surge_active": int(surge > 1), "surge_mult": surge if surge > 1 else None},
            ))

        return records

    async def _intercept_scrape(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        """Open Uber's web page and intercept the API call it makes internally."""
        intercepted = []

        async def handle_response(response: Response):
            url = response.url
            if any(k in url for k in ["product-estimates", "price-estimate", "fare", "estimate"]):
                try:
                    body = await response.json()
                    intercepted.append(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            # Navigate directly with lat/lng in URL — Uber supports this
            url = (
                f"{self.WEB_URL}"
                f"?pickup_latitude={od['origin']['lat']}"
                f"&pickup_longitude={od['origin']['lng']}"
                f"&dropoff_latitude={od['destination']['lat']}"
                f"&dropoff_longitude={od['destination']['lng']}"
            )
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(6)  # Wait for API calls to fire

        except Exception as e:
            self.logger.debug("[Uber] Page navigation failed: %s", e)

        for resp_data in intercepted:
            records = self._parse_api_response(resp_data, od, run_id)
            if records:
                return records

        # Final fallback: parse whatever text is on the page
        try:
            page_text = await page.inner_text("body")
            return self._parse_text(page_text, od, run_id)
        except Exception:
            return []

    def _parse_text(self, text: str, od: Dict, run_id: str) -> List[Dict]:
        records = []
        for m in re.finditer(
            r"(UberGo|UberX|Uber Auto|Uber Moto|Premier|UberXL|Comfort)[^\n]*?(₹[\d,]+(?:\s*[-–]\s*₹?[\d,]+)?)",
            text, re.IGNORECASE
        ):
            records.append(build_record(
                platform=self.platform_key, od=od,
                service_name=m.group(1), price_raw=m.group(2),
                run_id=run_id, surge=detect_surge(text),
            ))
        return records
