import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    """Load configuration settings from environment variables."""
    return {
        "db_path": os.getenv("CARGO_DB_PATH", "cargobot.db"),
        "email_server": os.getenv("EMAIL_SERVER", "imap.gmail.com"),
        "email_user": os.getenv("EMAIL_USER", ""),
        "email_pass": os.getenv("EMAIL_PASSWORD", ""),
        "email_folder": os.getenv("EMAIL_FOLDER", "INBOX"),
        "gpt_api_key": os.getenv("GPT_API_KEY", ""),
        "osrm_url": os.getenv("OSRM_URL", "http://router.project-osrm.org"),
        "default_rate": float(os.getenv("DEFAULT_RATE", "1.7")),
        "bad_rate": float(os.getenv("BAD_RATE", "1.5")),
        "high_demand_rate": float(os.getenv("HIGH_DEMAND_RATE", "2.0")),
        "search_radius": float(os.getenv("SEARCH_RADIUS", "200")),
        "whatsapp_export_path": os.getenv("WHATSAPP_EXPORT_PATH", "whatsapp_export.txt"),
        "web_platform_url": os.getenv("WEB_PLATFORM_URL", "http://example.com"),
    }

config = get_config()