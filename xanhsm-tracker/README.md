# XanhSM Price Intelligence Dashboard

Competitor ride pricing tracker for **Uber, Ola, Rapido** — auto-scraping across configured OD pairs at peak/off-peak times, with a live web dashboard.

```
GitHub Actions (scraper, cron) → Supabase (PostgreSQL) → Vercel (Next.js dashboard)
```

---

## Architecture

| Layer | Tech | Role |
|---|---|---|
| **Scraper** | Python + Playwright | Automates browser, extracts fares |
| **Schedule** | GitHub Actions (cron) | Runs scraper 8x/day, no server needed |
| **Database** | Supabase (free tier) | Stores all price snapshots |
| **Dashboard** | Next.js on Vercel | Live charts, table, surge alerts |

---

## Step-by-Step Deployment

### 1 — Set up Supabase (5 min)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Note down your **Project URL** and **API keys** (Settings → API)
3. Go to **SQL Editor** and run the contents of `scraper/supabase_migration.sql`
4. That creates the `price_snapshots` table with indexes and RLS policies.

You need two keys:
- **Anon key** → for the Next.js frontend (read-only)
- **Service role key** → for the Python scraper (write access) — keep this secret

---

### 2 — Push to GitHub (2 min)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/xanhsm-tracker.git
git push -u origin main
```

---

### 3 — Add GitHub Actions Secrets (2 min)

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name | Value |
|---|---|
| `SUPABASE_URL` | `https://your-project-id.supabase.co` |
| `SUPABASE_KEY` | Your Supabase **service_role** key |
| `SLACK_WEBHOOK` | (optional) Slack webhook for failure alerts |

---

### 4 — Deploy to Vercel (3 min)

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import your GitHub repo
3. Vercel will auto-detect Next.js — no build config needed
4. Add **Environment Variables** in Vercel project settings:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-project-id.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase **anon** key |

5. Click **Deploy** — done ✅

---

### 5 — Trigger your first scrape

Go to your GitHub repo → **Actions → Ride Price Scraper → Run workflow**

This runs manually and you can watch it scrape live. After it succeeds, your Vercel dashboard will show the first data points.

---

## Configuration

### Add/change OD pairs
Edit `scraper/config.py` → `OD_PAIRS`

```python
{
    "id": "my_route",
    "label": "From A → To B",
    "origin": {"lat": 28.xxx, "lng": 77.xxx, "address": "Full address, City"},
    "destination": {"lat": 28.xxx, "lng": 77.xxx, "address": "Full address, City"},
},
```

### Change scrape times
Edit `.github/workflows/scrape.yml` → `schedule` section
(Remember: GitHub cron is UTC. Subtract 5h 30min from IST.)

### Add a new city
1. Add OD pairs in `config.py`
2. Update the `OD_PAIRS` array in `app/page.tsx` so the dashboard filter shows them

---

## Local Development

```bash
# Frontend
cp .env.example .env.local   # fill in your Supabase keys
npm install
npm run dev                   # → http://localhost:3000

# Scraper (test locally)
cd scraper
pip install -r requirements.txt
playwright install chromium
SUPABASE_URL=xxx SUPABASE_KEY=xxx python main.py --platform uber --od cp_to_airport
```

---

## Cost

| Service | Plan | Cost |
|---|---|---|
| Supabase | Free tier | ₹0 (500MB DB, 2GB bandwidth) |
| Vercel | Hobby | ₹0 |
| GitHub Actions | Free tier | ₹0 (2,000 min/month — scraper uses ~5 min/run × 8 runs = 40 min/day, well within limit) |

**Total: ₹0/month** until you scale significantly.

---

## Upgrading Scraper Reliability

If Ola/Rapido web scraping is flaky, the next level is mitmproxy on an Android emulator:

1. Run Genymotion (Android emulator) on a small VM (DigitalOcean ~$6/mo)
2. Route app traffic through mitmproxy to intercept API calls
3. Replace the Playwright scraper with direct API replication
4. Much more stable — apps use their own APIs consistently

Open an issue or ping the team if you want to set this up.
