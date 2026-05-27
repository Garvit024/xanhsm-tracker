"""
BaseScraper — shared Playwright setup, stealth helpers, and result schema.
All platform scrapers inherit from this.
"""

import random
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import SCRAPER, USER_AGENTS, VIEWPORTS

IST = timedelta(hours=5, minutes=30)
logger = logging.getLogger(__name__)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def now_ist_hhmm() -> str:
    return (datetime.now(timezone.utc) + IST).strftime("%H:%M")

def make_run_id() -> str:
    return (datetime.now(timezone.utc) + IST).strftime("%Y%m%d_%H%M")


def parse_price(raw: str) -> Dict[str, Optional[float]]:
    """
    Parse a raw price string like '₹120', '₹120-150', '₹120 - ₹150'
    Returns {"price_min": 120.0, "price_max": 150.0}
    """
    nums = re.findall(r"[\d,]+(?:\.\d+)?", raw.replace(",", ""))
    floats = [float(n.replace(",", "")) for n in nums if n]
    if not floats:
        return {"price_min": None, "price_max": None}
    return {
        "price_min": floats[0],
        "price_max": floats[1] if len(floats) > 1 else None,
    }


def detect_surge(text: str) -> Dict[str, Any]:
    """Detect surge keywords and multiplier in page text."""
    text_lower = text.lower()
    surge_keywords = ["surge", "high demand", "peak pricing", "dynamic pricing", "busy"]
    active = any(k in text_lower for k in surge_keywords)
    mult = None
    # Look for patterns like "2.1x" or "1.8×"
    m = re.search(r"(\d+\.\d+)[x×]", text_lower)
    if m:
        mult = float(m.group(1))
    return {"surge_active": int(active), "surge_mult": mult}


def build_record(
    platform: str,
    od: Dict,
    service_name: str,
    price_raw: str,
    run_id: str,
    eta_minutes: Optional[int] = None,
    surge: Optional[Dict] = None,
    status: str = "ok",
    error_msg: str = None,
) -> Dict[str, Any]:
    prices = parse_price(price_raw) if price_raw else {"price_min": None, "price_max": None}
    surge = surge or {"surge_active": 0, "surge_mult": None}
    return {
        "scraped_at": now_utc(),
        "scraped_at_ist": now_ist_hhmm(),
        "platform": platform,
        "od_pair_id": od["id"],
        "od_label": od["label"],
        "service_name": service_name,
        "price_raw": price_raw,
        **prices,
        "eta_minutes": eta_minutes,
        **surge,
        "status": status,
        "error_msg": error_msg,
        "scrape_run_id": run_id,
    }


class BaseScraper(ABC):
    platform_key: str = ""
    platform_name: str = ""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _new_context(self, browser: Browser) -> BrowserContext:
        """Create a fresh, fingerprint-randomized browser context."""
        ua = random.choice(USER_AGENTS)
        vp = random.choice(VIEWPORTS)
        ctx = await browser.new_context(
            user_agent=ua,
            viewport=vp,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation=None,           # set per-OD inside scrape methods
            permissions=[],
            java_script_enabled=True,
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        # Basic stealth: mask webdriver flag
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """)
        return ctx

    async def _take_screenshot(self, page: Page, label: str):
        if SCRAPER.get("screenshot_on_failure"):
            path = f"logs/fail_{self.platform_key}_{label}_{make_run_id()}.png"
            await page.screenshot(path=path, full_page=True)
            self.logger.info("Screenshot saved: %s", path)

    @abstractmethod
    async def scrape_od(self, page: Page, od: Dict, run_id: str) -> List[Dict]:
        """Scrape all service categories for one OD pair. Return list of records."""
        ...

    async def run(self, od_pairs: List[Dict], run_id: str) -> List[Dict]:
        results = []
        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(
                headless=SCRAPER["headless"],
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )
            for od in od_pairs:
                for attempt in range(SCRAPER["retry_attempts"] + 1):
                    ctx = await self._new_context(browser)
                    page = await ctx.new_page()
                    page.set_default_timeout(SCRAPER["timeout_ms"])
                    try:
                        self.logger.info("[%s] Scraping %s (attempt %d)", self.platform_name, od["label"], attempt + 1)
                        records = await self.scrape_od(page, od, run_id)
                        results.extend(records)
                        break
                    except Exception as e:
                        self.logger.warning("[%s] Failed %s: %s", self.platform_name, od["label"], e)
                        await self._take_screenshot(page, od["id"])
                        if attempt == SCRAPER["retry_attempts"]:
                            # Record the failure so we know it was attempted
                            results.append(build_record(
                                platform=self.platform_key,
                                od=od,
                                service_name="ALL",
                                price_raw=None,
                                run_id=run_id,
                                status="failed",
                                error_msg=str(e),
                            ))
                    finally:
                        await ctx.close()
            await browser.close()
        return results
