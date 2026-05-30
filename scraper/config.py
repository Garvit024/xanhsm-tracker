"""
XanhSM Competitive Pricing Scraper — Configuration
"""

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

SCHEDULE_TIMES = [
    "07:00", "09:00", "12:00", "14:00",
    "17:30", "19:00", "21:00", "23:30",
]

PLATFORMS = {
    "uber":   {"enabled": True,  "name": "Uber",   "service_categories": ["UberGo", "Uber Auto", "Premier", "UberXL", "Uber Moto"]},
    "ola":    {"enabled": True,  "name": "Ola",    "service_categories": ["Mini", "Sedan", "Prime", "Auto", "Ola Bike"]},
    "rapido": {"enabled": True,  "name": "Rapido", "service_categories": ["Bike", "Auto", "Cab Economy", "Cab+"]},
}

SCRAPER = {
    "headless": True,
    "timeout_ms": 20000,        # Reduced from 30s to 20s
    "wait_after_load_s": 3,
    "retry_attempts": 1,        # Reduced retries — fail faster
    "retry_delay_s": 3,
    "screenshot_on_failure": False,  # Off in CI to keep things lean
}

STORAGE = {
    "sqlite_path": "data/prices.db",
    "csv_export_path": "data/prices_export.csv",
    "log_path": "logs/scraper.log",
}

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Samsung SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
]

VIEWPORTS = [
    {"width": 390, "height": 844},
    {"width": 412, "height": 915},
]
