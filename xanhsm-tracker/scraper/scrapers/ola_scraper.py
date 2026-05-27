"""
Ola Scraper
────────────
Targets book.olacabs.com — Ola's web booking interface.

Strategy:
  1. Navigate to booking page
  2. Fill pickup/drop with address strings
  3. Trigger price fetch (Ola fires an API call when both fields filled)
  4. Intercept or parse the network response / DOM for fares

Note: Ola's web UI is less stable than Uber's. If it consistently blocks,
the mitmproxy / API approach is more reliable for Ola.
"""

import asyncio
import json
import re
from typing import List, Dict, Optional

from playwright.async_api import Page, Response

from scrapers.base import BaseScraper, build_record, detect_surge
from config import SCRAPER


class OlaScraper(BaseScraper):
    platform_key = "ola"
    platform_name = "Ola"
    BASE_URL = "https://book.olacabs.com/"

    async def scrape_od(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        intercepted_fares = []

        # ── Intercept Ola's internal pricing API ─────────────────────────────
        async def handle_response(response: Response):
            url = response.url
            if any(k in url for k in ["eta_v2", "fare", "pricing", "categories", "estimate"]):
                try:
                    body = await response.json()
                    intercepted_fares.append(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        await page.goto(self.BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        # ── Handle cookie/location popups ─────────────────────────────────────
        for dismiss_sel in ['button:has-text("Allow")', 'button:has-text("Accept")', '[class*="close" i]']:
            try:
                btn = page.locator(dismiss_sel).first
                if await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

        # ── Fill Pickup ───────────────────────────────────────────────────────
        pickup = page.locator('input[placeholder*="pickup" i], input[id*="pickup" i], input[name*="pickup" i]').first
        await pickup.click()
        await pickup.fill(od["origin"]["address"])
        await asyncio.sleep(2)
        try:
            sug = page.locator('[class*="suggestion" i], [class*="pac-item" i], [role="option"]').first
            await sug.wait_for(state="visible", timeout=6000)
            await sug.click()
        except Exception:
            await page.keyboard.press("Enter")
        await asyncio.sleep(1)

        # ── Fill Drop ─────────────────────────────────────────────────────────
        drop = page.locator('input[placeholder*="drop" i], input[placeholder*="destination" i], input[id*="drop" i]').first
        await drop.click()
        await drop.fill(od["destination"]["address"])
        await asyncio.sleep(2)
        try:
            sug2 = page.locator('[class*="suggestion" i], [class*="pac-item" i], [role="option"]').first
            await sug2.wait_for(state="visible", timeout=6000)
            await sug2.click()
        except Exception:
            await page.keyboard.press("Enter")

        # ── Wait for prices to load ───────────────────────────────────────────
        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        records = []

        # Try intercepted API responses first
        if intercepted_fares:
            records = self._parse_api_responses(intercepted_fares, od, run_id)

        # Fallback: DOM scraping
        if not records:
            records = await self._parse_dom(page, od, run_id)

        self.logger.info("[Ola] %s → got %d service records", od["label"], len(records))
        return records

    def _parse_api_responses(self, responses: List[Dict], od: Dict, run_id: str) -> List[Dict]:
        """Parse intercepted Ola API JSON responses."""
        records = []
        for resp in responses:
            # Ola's pricing API returns categories array
            categories = (
                resp.get("data", {}).get("categories") or
                resp.get("categories") or
                resp.get("data", [])
            )
            if not isinstance(categories, list):
                continue
            for cat in categories:
                name = cat.get("display_name") or cat.get("name") or cat.get("category_display_name", "Unknown")
                fare = cat.get("fare") or cat.get("amount") or cat.get("estimated_fare", {})
                if isinstance(fare, dict):
                    price_raw = f"₹{fare.get('min', '')} - ₹{fare.get('max', fare.get('min', ''))}"
                elif fare:
                    price_raw = f"₹{fare}"
                else:
                    price_raw = None

                eta = cat.get("eta") or cat.get("pickup_eta")
                surge = {
                    "surge_active": int(cat.get("surge_factor", 1) > 1),
                    "surge_mult": cat.get("surge_factor"),
                }
                records.append(build_record(
                    platform=self.platform_key,
                    od=od,
                    service_name=name,
                    price_raw=price_raw,
                    run_id=run_id,
                    eta_minutes=int(eta / 60) if eta and eta > 60 else eta,
                    surge=surge,
                ))
        return records

    async def _parse_dom(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        """Fallback DOM scraping for Ola fare cards."""
        records = []
        page_text = await page.inner_text("body")
        surge_info = detect_surge(page_text)

        cards = await page.locator('[class*="category" i], [class*="cab-type" i], [class*="ride-type" i]').all()
        for card in cards:
            try:
                text = await card.inner_text()
                name_m = re.search(r"(Mini|Prime|Sedan|Auto|Bike|Ola\s?\w+)", text, re.IGNORECASE)
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
