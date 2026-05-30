"""
Supabase storage layer — replaces storage.py for cloud deployment.
Uses the Supabase REST API via supabase-py.

Set these environment variables (GitHub Actions Secrets):
  SUPABASE_URL   — e.g. https://xxxx.supabase.co
  SUPABASE_KEY   — service_role key (NOT anon — needs write access)
"""

import os
import logging
from typing import List, Dict, Any

from supabase import create_client, Client

logger = logging.getLogger(__name__)

TABLE = "price_snapshots"

def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set as environment variables.")
    return create_client(url, key)


def insert_prices(records: List[Dict[str, Any]]):
    """Batch upsert price records to Supabase."""
    client = get_client()
    # Supabase insert in batches of 100
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        # Remove None values that Supabase might reject
        clean_batch = [{k: v for k, v in r.items() if v is not None or k in ('price_min', 'price_max')} for r in batch]
        res = client.table(TABLE).insert(clean_batch).execute()
        if hasattr(res, 'error') and res.error:
            logger.error("Supabase insert error: %s", res.error)
        else:
            logger.info("Inserted batch of %d records", len(batch))

    logger.info("Total: inserted %d records to Supabase", len(records))


def export_csv(output_path: str = "data/prices_export.csv"):
    """Pull all data from Supabase and write to CSV."""
    import csv, os
    client = get_client()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    res = client.table(TABLE).select("*").order("scraped_at", desc=True).execute()
    rows = res.data or []
    if not rows:
        logger.warning("No data to export")
        return
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Exported %d rows to %s", len(rows), output_path)
    return output_path
