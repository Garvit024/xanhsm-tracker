-- Run this once in Supabase → SQL Editor
-- Creates the price_snapshots table and indexes

CREATE TABLE IF NOT EXISTS price_snapshots (
  id              BIGSERIAL PRIMARY KEY,
  scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  scraped_at_ist  TEXT NOT NULL,
  platform        TEXT NOT NULL,
  od_pair_id      TEXT NOT NULL,
  od_label        TEXT NOT NULL,
  service_name    TEXT NOT NULL,
  price_min       NUMERIC,
  price_max       NUMERIC,
  price_raw       TEXT,
  eta_minutes     INTEGER,
  surge_active    INTEGER DEFAULT 0,
  surge_mult      NUMERIC,
  status          TEXT DEFAULT 'ok',
  error_msg       TEXT,
  scrape_run_id   TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_platform_od_time
  ON price_snapshots (platform, od_pair_id, scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_scrape_run
  ON price_snapshots (scrape_run_id);

CREATE INDEX IF NOT EXISTS idx_status
  ON price_snapshots (status);

-- Enable Row Level Security (allow public read, service_role write)
ALTER TABLE price_snapshots ENABLE ROW LEVEL SECURITY;

-- Policy: anyone can read (for the Next.js dashboard via anon key)
CREATE POLICY "Public read" ON price_snapshots
  FOR SELECT USING (true);

-- Policy: only service_role can insert (used by Python scraper)
CREATE POLICY "Service insert" ON price_snapshots
  FOR INSERT WITH CHECK (true);

-- Optional: auto-delete records older than 90 days (keeps DB lean)
-- Uncomment if you want automatic cleanup:
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-old-prices', '0 2 * * *',
--   $$DELETE FROM price_snapshots WHERE scraped_at < NOW() - INTERVAL '90 days'$$);
