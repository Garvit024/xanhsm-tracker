"""
Uber Scraper
────────────
Uses Uber's web-based price estimator (uber.com/in/en/price-estimate/).
This is the most scrapeable platform because Uber has a proper web UI.

Strategy:
  1. Open price-estimate page
  2. Type origin → pick first autocomplete suggestion
  3. Type destination → pick first suggestion
  4. Wait for fare cards to load
  5. Extract service name, price range, ETA, surge indicator per card
"""

import asyncio
import re
from typing import List, Dict

from playwright.async_api import Page

from scrapers.base import BaseScraper, build_record, detect_surge
from config import SCRAPER


class UberScraper(BaseScraper):
    platform_key = "uber"
    platform_name = "Uber"
    BASE_URL = "https://www.uber.com/in/en/price-estimate/"

    async def scrape_od(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        await page.goto(self.BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        # ── Fill Origin ──────────────────────────────────────────────────────
        origin_input = page.locator('input[placeholder*="Pickup" i], input[name*="pickup" i], input[id*="pickup" i]').first
        await origin_input.click()
        await origin_input.fill(od["origin"]["address"])
        await asyncio.sleep(1.5)
        # Pick first dropdown suggestion
        suggestion = page.locator('[class*="suggestion" i], [class*="result" i], [role="option"]').first
        await suggestion.wait_for(state="visible", timeout=8000)
        await suggestion.click()
        await asyncio.sleep(1)

        # ── Fill Destination ─────────────────────────────────────────────────
        dest_input = page.locator('input[placeholder*="Destination" i], input[placeholder*="dropoff" i], input[name*="destination" i]').first
        await dest_input.click()
        await dest_input.fill(od["destination"]["address"])
        await asyncio.sleep(1.5)
        suggestion2 = page.locator('[class*="suggestion" i], [class*="result" i], [role="option"]').first
        await suggestion2.wait_for(state="visible", timeout=8000)
        await suggestion2.click()
        await asyncio.sleep(SCRAPER["wait_after_load_s"])

        # ── Wait for fare cards ──────────────────────────────────────────────
        # Uber renders a list of product cards after both inputs are filled
        try:
            await page.wait_for_selector('[class*="PriceEstimateCard" i], [class*="fare-card" i], [data-testid*="price" i]', timeout=15000)
        except Exception:
            # Fallback: just wait and try anyway
            await asyncio.sleep(3)

        # ── Extract fare data ────────────────────────────────────────────────
        records = []
        page_text = await page.inner_text("body")
        surge_info = detect_surge(page_text)

        # Try to get individual service cards
        cards = await page.locator('[class*="PriceEstimateCard" i], [class*="fare-card" i], [class*="product-card" i]').all()

        if cards:
            for card in cards:
                try:
                    card_text = await card.inner_text()
                    service = await self._extract_service_name(card)
                    price = await self._extract_price(card)
                    eta = await self._extract_eta(card)
                    records.append(build_record(
                        platform=self.platform_key,
                        od=od,
                        service_name=service or "Unknown",
                        price_raw=price,
                        run_id=run_id,
                        eta_minutes=eta,
                        surge=detect_surge(card_text),
                    ))
                except Exception as e:
                    self.logger.debug("Card parse error: %s", e)
        else:
            # Fallback: parse entire page text with regex
            records = self._parse_page_text_fallback(page_text, od, run_id, surge_info)

        self.logger.info("[Uber] %s → got %d service records", od["label"], len(records))
        return records

    async def _extract_service_name(self, card) -> str:
        for sel in ['[class*="product-name" i]', '[class*="ProductName" i]', 'h3', 'h4', 'strong']:
            el = card.locator(sel).first
            if await el.count():
                return (await el.inner_text()).strip()
        return "Unknown"

    async def _extract_price(self, card) -> str:
        for sel in ['[class*="price" i]', '[class*="fare" i]', '[class*="Price" i]']:
            el = card.locator(sel).first
            if await el.count():
                text = (await el.inner_text()).strip()
                if re.search(r"[\d₹]", text):
                    return text
        # Last resort: find ₹ pattern in card text
        text = await card.inner_text()
        m = re.search(r"₹[\d,]+(?:\s*[-–]\s*₹?[\d,]+)?", text)
        return m.group(0) if m else None

    async def _extract_eta(self, card) -> int:
        text = await card.inner_text()
        m = re.search(r"(\d+)\s*min", text, re.IGNORECASE)
        return int(m.group(1)) if m else None

    def _parse_page_text_fallback(self, text: str, od: Dict, run_id: str, surge_info: Dict) -> List[Dict]:
        """Crude regex fallback when DOM selectors don't match."""
        records = []
        patterns = [
            (r"(UberGo|UberX|Premier|Uber XL|Uber Auto|Uber Moto|UberPool).*?(₹[\d,]+(?:\s*[-–]\s*₹?[\d,]+)?)", re.IGNORECASE),
        ]
        for pat, flags in patterns:
            for m in re.finditer(pat, text, flags):
                records.append(build_record(
                    platform=self.platform_key,
                    od=od,
                    service_name=m.group(1).strip(),
                    price_raw=m.group(2).strip(),
                    run_id=run_id,
                    surge=surge_info,
                ))
        return records
