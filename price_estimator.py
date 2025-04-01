from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

def estimate_price(distance):
    """Estimate the price of a load based on distance.

    Args:
        distance (float): Distance in kilometers.

    Returns:
        float: Estimated price in EUR, or None if distance is invalid.
    """
    try:
        if distance and distance > 0:
            return distance * config["default_rate"]
        return None
    except Exception as e:
        logging.error(f"Error estimating price: {e}")
        return None