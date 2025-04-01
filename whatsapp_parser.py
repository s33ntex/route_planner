import re
from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

def parse_whatsapp_message(message):
    """Parse a WhatsApp message to extract offer details.

    Args:
        message (str): WhatsApp message text.

    Returns:
        dict: Parsed offer data or None if parsing fails.
    """
    try:
        # Example format: "[Group Name] Load from Berlin to Hamburg, 595€, LF8, today, extra info"
        pattern = r"\[(.*?)\].*?from (\w+) to (\w+)(?:, (\d+)€)?(?:, (LF\d+))?(?:, (\w+))?(?:, (.*))?"
        match = re.search(pattern, message)
        if match:
            return {
                "source": "whatsapp",
                "sender": match.group(1),  # Group name
                "loading_city": match.group(2),
                "unloading_city": match.group(3),
                "price": float(match.group(4)) if match.group(4) else None,
                "lf_number": match.group(5) if match.group(5) else None,
                "urgency": match.group(6) if match.group(6) else None,
                "additional_info": match.group(7) if match.group(7) else None
            }
        return None
    except Exception as e:
        logging.error(f"Error parsing WhatsApp message: {e}")
        return None

def process_whatsapp_file(file_path):
    """Process a WhatsApp export file to extract offers.

    Args:
        file_path (str): Path to the WhatsApp export file.

    Returns:
        list: List of parsed offers.
    """
    try:
        with open(file_path, "r") as f:
            messages = f.readlines()
        offers = []
        for msg in messages:
            parsed = parse_whatsapp_message(msg.strip())
            if parsed:
                offers.append(parsed)
        return offers
    except Exception as e:
        logging.error(f"Error processing WhatsApp file {file_path}: {e}")
        return []