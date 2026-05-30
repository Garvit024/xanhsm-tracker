"""
Rapido Scraper
──────────────
Rapido is highly mobile/app-first. Their web (rapido.bike) has limited
price visibility. Two strategies run in sequence:

  1. Network interception — capture any fare/eta API calls Rapido makes
     when location and destination are provided.
  2. DOM scraping — parse whatever fare cards appear in the web UI.

If both fail for a route, the record is logged as failed for tracking.
Tip: For Rapido, the mitmproxy approach on a real/emulated Android device
     will give the most consistent results.
"""

import asyncio
import re
from typing import List, Dict

from playwright.async_api import Page, Response

from scrapers.base import BaseScraper, build_record, detect_surge
from config import SCRAPER


class RapidoScraper(BaseScraper):
    platform_key = "rapido"
    platform_name = "Rapido"
    BASE_URL = "https://rapido.bike/"

    async def scrape_od(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        intercepted = []

        async def handle_response(response: Response):
            url = response.url
            if any(k in url for k in ["fare", "price", "estimate", "eta", "categories", "vehicle"]):
                try:
                    body = await response.json()
                    intercepted.append(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        # Set geolocation to origin (helps Rapido show local pricing)
        await page.context.set_geolocation({
            "latitude": od["origin"]["lat"],
            "longitude": od["origin"]["lng"],
        })
        await page.context.grant_permissions(["geolocation"])

        await page.goto(self.BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        # Dismiss popups
        for sel in ['button:has-text("Allow")', 'button:has-text("OK")', '[class*="close" i]']:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

        # ── Try to fill pickup / destination ──────────────────────────────────
        for ph in ["pickup", "from", "where are you", "pick up"]:
            try:
                inp = page.locator(f'input[placeholder*="{ph}" i]').first
                if await inp.is_visible():
                    await inp.click()
                    await inp.fill(od["origin"]["address"])
                    await asyncio.sleep(2)
                    sug = page.locator('[class*="suggestion" i], [class*="result" i], [role="option"]').first
                    if await sug.is_visible():
                        await sug.click()
                    break
            except Exception:
                continue

        for ph in ["drop", "destination", "where to", "drop off"]:
            try:
                inp = page.locator(f'input[placeholder*="{ph}" i]').first
                if await inp.is_visible():
                    await inp.click()
                    await inp.fill(od["destination"]["address"])
                    await asyncio.sleep(2)
                    sug = page.locator('[class*="suggestion" i], [class*="result" i], [role="option"]').first
                    if await sug.is_visible():
                        await sug.click()
                    break
            except Exception:
                continue

        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        records = []

        # Try intercepted API data first
        if intercepted:
            records = self._parse_api_responses(intercepted, od, run_id)

        # DOM fallback
        if not records:
            records = await self._parse_dom(page, od, run_id)

        self.logger.info("[Rapido] %s → got %d service records", od["label"], len(records))
        return records

    def _parse_api_responses(self, responses: List[Dict], od: Dict, run_id: str) -> List[Dict]:
        records = []
        for resp in responses:
            # Try common Rapido response shapes
            vehicles = (
                resp.get("vehicles") or
                resp.get("data", {}).get("vehicles") or
                resp.get("categories") or
                resp.get("data", [])
            )
            if not isinstance(vehicles, list):
                continue
            for v in vehicles:
                name = v.get("type") or v.get("vehicle_type") or v.get("display_name", "Unknown")
                fare_obj = v.get("fare") or v.get("estimated_fare") or {}
                if isinstance(fare_obj, dict):
                    lo = fare_obj.get("min") or fare_obj.get("amount_min")
                    hi = fare_obj.get("max") or fare_obj.get("amount_max")
                    price_raw = f"₹{lo}" + (f" - ₹{hi}" if hi and hi != lo else "")
                elif isinstance(fare_obj, (int, float)):
                    price_raw = f"₹{fare_obj}"
                else:
                    price_raw = str(v.get("price") or "")

                eta = v.get("eta") or v.get("pickup_eta")
                surge_mult = v.get("surge") or v.get("surge_multiplier")

                records.append(build_record(
                    platform=self.platform_key,
                    od=od,
                    service_name=str(name).title(),
                    price_raw=price_raw or None,
                    run_id=run_id,
                    eta_minutes=eta,
                    surge={"surge_active": int(bool(surge_mult and surge_mult > 1)), "surge_mult": surge_mult},
                ))
        return records

    async def _parse_dom(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        records = []
        page_text = await page.inner_text("body")
        surge_info = detect_surge(page_text)

        # Look for Rapido vehicle type cards
        cards = await page.locator('[class*="vehicle" i], [class*="ride-option" i], [class*="service-card" i]').all()
        for card in cards:
            try:
                text = await card.inner_text()
                name_m = re.search(r"(Bike|Auto|Cab|Economy|Cab\+|E-Bike|Rapido\s?\w+)", text, re.IGNORECASE)
                price_m = re.search(r"₹[\d,]+(?:\s*[-–]\s*₹?[\d,]+)?", text)
                eta_m = re.search(r"(\d+)\s*min", text, re.IGNORECASE)
                records.append(build_record(
                    platform=self.platform_key,
                    od=od,
                    service_name=name_m.group(0) if name_m else "Unknown",
                    price_raw=price_m.group(0) if price_m else None,
                    run_id=run_id,
                    eta_minutes=int(eta_m.group(1)) if eta_m else None,
                    surge=surge_info,
                ))
            except Exception:
                pass

        return records
