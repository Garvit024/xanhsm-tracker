"""
XanhSM Scraper — Supabase Edition
Designed to run inside GitHub Actions.

Usage:
  python main.py                   # All platforms, all OD pairs
  python main.py --platform uber   # Single platform
  python main.py --od cp_to_airport
"""

import asyncio
import argparse
import logging
import os
import sys

# Add scraper dir to path
sys.path.insert(0, os.path.dirname(__file__))

from config import OD_PAIRS, PLATFORMS
from scrapers import UberScraper, OlaScraper, RapidoScraper
from storage_supabase import insert_prices
from scrapers.base import make_run_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("main")

SCRAPER_MAP = {
    "uber":   UberScraper,
    "ola":    OlaScraper,
    "rapido": RapidoScraper,
}


async def run_all(platforms=None, od_ids=None):
    run_id = make_run_id()
    logger.info("═══ Starting scrape run %s ═══", run_id)

    target_platforms = platforms or [k for k, v in PLATFORMS.items() if v["enabled"]]
    target_ods = [od for od in OD_PAIRS if (not od_ids or od["id"] in od_ids)]

    all_records = []
    for platform_key in target_platforms:
        if platform_key not in SCRAPER_MAP:
            continue
        scraper = SCRAPER_MAP[platform_key]()
        try:
            records = await scraper.run(target_ods, run_id)
            all_records.extend(records)
            ok = sum(1 for r in records if r["status"] == "ok")
            logger.info("[%s] ✓ %d ok | ✗ %d failed", platform_key.upper(), ok, len(records) - ok)
        except Exception as e:
            logger.error("[%s] Scraper crashed: %s", platform_key, e, exc_info=True)

    if all_records:
        insert_prices(all_records)
        logger.info("═══ Run %s complete — %d records saved ═══", run_id, len(all_records))
    else:
        logger.warning("═══ Run %s — no records collected ═══", run_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", nargs="+", choices=list(SCRAPER_MAP.keys()))
    parser.add_argument("--od", nargs="+")
    args = parser.parse_args()
    asyncio.run(run_all(platforms=args.platform, od_ids=args.od))


if __name__ == "__main__":
    main()
