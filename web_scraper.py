from bs4 import BeautifulSoup
import requests
from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

def scrape_web_platform(url):
    """Scrape the web platform to extract offers.

    Args:
        url (str): URL of the web platform.

    Returns:
        list: List of parsed offers.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")  # Adjust based on actual HTML structure
        if not table:
            logging.warning("No table found on web platform.")
            return []
        offers = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
            offers.append({
                "source": "web",
                "sender": "Fracht",
                "loading_city": cols[1].text.split(",")[1].strip(),  # e.g., "DE, Mosel/Zwickau" -> "Mosel/Zwickau"
                "unloading_city": cols[2].text.split(",")[1].strip(),
                "price": float(cols[3].text.replace(" EUR", "").replace(",", "")) if cols[3].text else None,
                "lf_number": None,  # Not provided in table
                "urgency": cols[4].text if cols[4].text else None,  # Load from date as urgency
                "additional_info": None
            })
        return offers
    except Exception as e:
        logging.error(f"Error scraping web platform: {e}")
        return []