from datetime import timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

class RiskAssessor:
    """Assesses risks based on return load availability."""
    def __init__(self, db):
        """Initialize RiskAssessor with a database connection.

        Args:
            db (Database): Database instance.
        """
        self.db = db

    def assess_return_load_risk(self, city_id, days=7):
        """Assess the risk of not finding a return load from a city.

        Args:
            city_id (int): ID of the city.
            days (int): Number of days to look back.

        Returns:
            str: Risk level ('High', 'Medium', 'Low').
        """
        try:
            count = self.db.count_offers_from_city(city_id, days)
            if count < 3:
                return "High"
            elif count <= 10:
                return "Medium"
            return "Low"
        except Exception as e:
            logging.error(f"Error assessing return load risk for city {city_id}: {e}")
            return "Unknown"