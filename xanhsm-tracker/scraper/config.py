"""
XanhSM Competitive Pricing Scraper — Configuration
Edit this file to add/remove OD pairs, time slots, and platforms.
"""

# ─── OD Pairs ───────────────────────────────────────────────────────────────
# lat/lng for Playwright-based scrapers; address strings for display
OD_PAIRS = [
    {
        "id": "cp_to_airport",
        "label": "Connaught Place → IGI Airport",
        "origin": {"lat": 28.6315, "lng": 77.2167, "address": "Connaught Place, New Delhi"},
        "destination": {"lat": 28.5562, "lng": 77.1000, "address": "IGI Airport, New Delhi"},
    },
    {
        "id": "gurgaon_cyber_to_dlf",
        "label": "Cyber City → DLF Phase 2",
        "origin": {"lat": 28.4950, "lng": 77.0888, "address": "Cyber City, Gurugram"},
        "destination": {"lat": 28.4823, "lng": 77.0927, "address": "DLF Phase 2, Gurugram"},
    },
    {
        "id": "noida_sec18_to_cp",
        "label": "Noida Sector 18 → Connaught Place",
        "origin": {"lat": 28.5672, "lng": 77.3211, "address": "Sector 18, Noida"},
        "destination": {"lat": 28.6315, "lng": 77.2167, "address": "Connaught Place, New Delhi"},
    },
    {
        "id": "lajpat_to_gurgaon_huda",
        "label": "Lajpat Nagar → HUDA City Centre",
        "origin": {"lat": 28.5700, "lng": 77.2436, "address": "Lajpat Nagar, New Delhi"},
        "destination": {"lat": 28.4594, "lng": 77.0266, "address": "HUDA City Centre, Gurugram"},
    },
]

# ─── Time Slots for Scheduled Runs ──────────────────────────────────────────
# Scraper will run at these times (24-hr HH:MM, IST)
SCHEDULE_TIMES = [
    "07:00",  # Morning pre-peak
    "09:00",  # Morning peak
    "12:00",  # Midday
    "14:00",  # Post-lunch
    "17:30",  # Evening pre-peak
    "19:00",  # Evening peak
    "21:00",  # Night
    "23:30",  # Late night
]

# ─── Platform Configs ────────────────────────────────────────────────────────
PLATFORMS = {
    "uber": {
        "enabled": True,
        "name": "Uber",
        "base_url": "https://www.uber.com/in/en/price-estimate/",
        # Service categories to capture (as they appear in Uber's UI)
        "service_categories": ["UberGo", "Uber Auto", "Premier", "UberXL", "Uber Moto"],
    },
    "ola": {
        "enabled": True,
        "name": "Ola",
        "base_url": "https://book.olacabs.com/",
        "service_categories": ["Mini", "Sedan", "Prime", "Auto", "Ola Bike"],
    },
    "rapido": {
        "enabled": True,
        "name": "Rapido",
        "base_url": "https://rapido.bike/",
        "service_categories": ["Bike", "Auto", "Cab Economy", "Cab+"],
    },
}

# ─── Scraper Settings ────────────────────────────────────────────────────────
SCRAPER = {
    "headless": True,           # Set False to watch browser (useful for debugging)
    "timeout_ms": 30000,        # Page load timeout in ms
    "wait_after_load_s": 4,     # Seconds to wait after page loads (for JS to settle)
    "retry_attempts": 2,        # Retries per platform per OD pair
    "retry_delay_s": 5,         # Delay between retries
    "screenshot_on_failure": True,  # Save screenshot when scrape fails
}

# ─── Storage ─────────────────────────────────────────────────────────────────
STORAGE = {
    "sqlite_path": "data/prices.db",
    "csv_export_path": "data/prices_export.csv",
    "log_path": "logs/scraper.log",
}

# ─── Browser Fingerprint Rotation ────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Samsung SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
]

VIEWPORTS = [
    {"width": 390, "height": 844},   # iPhone 14
    {"width": 412, "height": 915},   # Pixel 7
    {"width": 360, "height": 780},   # Samsung Galaxy
]
