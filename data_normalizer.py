from geopy.geocoders import Nominatim
from routingpy import OSRM
from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

geolocator = Nominatim(user_agent="cargobot")
osrm = OSRM(base_url=config["osrm_url"])

class DataNormalizer:
    """Normalizes offer data, including city names and distances."""
    def __init__(self, db):
        """Initialize DataNormalizer with a database connection.

        Args:
            db (Database): Database instance.
        """
        self.db = db
        self.city_cache = {}

    def normalize_city(self, city_name):
        """Normalize city name using cache, database, or geocoding API.

        Args:
            city_name (str): The name of the city to normalize.

        Returns:
            tuple: City data (id, name, country_code, lat, lon) or None if not found.
        """
        if city_name in self.city_cache:
            return self.city_cache[city_name]

        city = self.db.get_city_by_alias(city_name) or self.db.get_city_by_name(city_name)
        if city:
            self.city_cache[city_name] = city
            return city

        try:
            location = geolocator.geocode(city_name)
            if location:
                city_name_clean = location.address.split(",")[0]
                city_id = self.db.insert_city(city_name_clean, "XX", location.latitude, location.longitude)
                self.db.insert_alias(city_name, city_id)
                city = (city_id, city_name_clean, "XX", location.latitude, location.longitude)
                self.city_cache[city_name] = city
                return city
        except Exception as e:
            logging.error(f"Error geocoding {city_name}: {e}")
        return None

    def process_offer(self, offer_data, raw_message=None):
        """Process offer data, normalizing cities and calculating distance.

        Args:
            offer_data (dict): Offer details including loading_city, unloading_city, etc.
            raw_message (str, optional): Raw message text for reference.

        Returns:
            dict: Processed offer data or None if normalization fails.
        """
        loading_city = self.normalize_city(offer_data["loading_city"])
        unloading_city = self.normalize_city(offer_data["unloading_city"])
        if not loading_city or not unloading_city:
            logging.warning(f"Failed to normalize cities: {offer_data['loading_city']} to {offer_data['unloading_city']}")
            return None

        coords1 = (loading_city[4], loading_city[3])  # lon, lat
        coords2 = (unloading_city[4], unloading_city[3])  # lon, lat
        distance = None
        try:
            route = osrm.route(locations=[coords1, coords2], profile="driving")
            distance = route.distance / 1000  # Convert meters to km
        except Exception as e:
            logging.error(f"Error calculating route: {e}")

        return {
            "source": offer_data.get("source", "unknown"),
            "sender": offer_data.get("sender", "unknown"),
            "loading_city_id": loading_city[0],
            "unloading_city_id": unloading_city[0],
            "price": offer_data.get("price"),
            "lf_number": offer_data.get("lf_number"),
            "urgency": offer_data.get("urgency"),
            "distance": distance,
            "estimated_price": distance * config["default_rate"] if distance and not offer_data.get("price") else None,
            "additional_info": offer_data.get("additional_info"),
            "raw_message": raw_message
        }