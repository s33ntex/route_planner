from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

class RoutePlanner:
    """Plans routes for loads based on offers in the database."""
    def __init__(self, db):
        """Initialize RoutePlanner with a database connection.

        Args:
            db (Database): Database instance.
        """
        self.db = db

    def find_single_load_anywhere(self, start_city_id):
        """Find the best loads from a starting city to anywhere.

        Args:
            start_city_id (int): ID of the starting city.

        Returns:
            list: List of top offers, sorted by profitability.
        """
        try:
            offers = self.db.get_offers_by_loading_city(start_city_id)
            formatted_offers = [self._format_offer(offer) for offer in offers]
            return sorted(
                formatted_offers,
                key=lambda x: x["price_per_km"] if x["price_per_km"] else 0,
                reverse=True
            )[:5]
        except Exception as e:
            logging.error(f"Error finding single load from city {start_city_id}: {e}")
            return []

    def find_single_load_a_to_b(self, start_city_id, end_city_id):
        """Find a route from start city to end city, either direct or via one intermediate city.

        Args:
            start_city_id (int): ID of the starting city.
            end_city_id (int): ID of the destination city.

        Returns:
            list: List of routes (direct or indirect).
        """
        try:
            direct_offers = [o for o in self.db.get_offers_by_loading_city(start_city_id) if o[5] == end_city_id]
            if direct_offers:
                return [self._format_offer(o) for o in direct_offers]

            # Try indirect route (A → C → B)
            intermediate_offers = []
            for offer_a in self.db.get_offers_by_loading_city(start_city_id):
                for offer_b in self.db.get_offers_by_loading_city(offer_a[5]):
                    if offer_b[5] == end_city_id:
                        route = self._combine_offers(offer_a, offer_b)
                        if route["price_per_km"] >= config["bad_rate"]:
                            intermediate_offers.append(route)
            return intermediate_offers[:1]
        except Exception as e:
            logging.error(f"Error finding route from {start_city_id} to {end_city_id}: {e}")
            return []

    def find_multi_leg_route(self, start_city_id, max_legs=3):
        """Build a multi-leg route starting from a city.

        Args:
            start_city_id (int): ID of the starting city.
            max_legs (int): Maximum number of legs in the route.

        Returns:
            dict: Multi-leg route with segments, total distance, and revenue.
        """
        try:
            route = {"segments": [], "total_distance": 0, "total_revenue": 0}
            current_city = start_city_id
            for _ in range(max_legs):
                offers = self.db.get_offers_by_loading_city(current_city)
                if not offers:
                    break
                best_offer = max([self._format_offer(o) for o in offers], 
                                key=lambda x: x["price_per_km"] if x["price_per_km"] else 0, 
                                default=None)
                if not best_offer:
                    break
                route["segments"].append(best_offer)
                route["total_distance"] += best_offer["distance"] or 0
                route["total_revenue"] += best_offer["price"] or best_offer["estimated_price"] or 0
                current_city = best_offer["unloading_city_id"]
            if route["total_distance"] > 0 and route["segments"]:
                route["price_per_km"] = route["total_revenue"] / route["total_distance"]
                return route
            return None
        except Exception as e:
            logging.error(f"Error building multi-leg route from {start_city_id}: {e}")
            return None

    def _format_offer(self, offer):
        """Format an offer for display or further processing.

        Args:
            offer (tuple): Offer data from the database.

        Returns:
            dict: Formatted offer data.
        """
        try:
            price = offer[6] or offer[10]  # price or estimated_price
            distance = offer[9]
            price_per_km = price / distance if price and distance else None
            return {
                "loading_city_id": offer[4],
                "unloading_city_id": offer[5],
                "distance": distance,
                "price": offer[6],
                "estimated_price": offer[10],
                "price_per_km": price_per_km,
                "lf_number": offer[7],
                "urgency": offer[8],
                "additional_info": offer[11]
            }
        except Exception as e:
            logging.error(f"Error formatting offer: {e}")
            return {}

    def _combine_offers(self, offer_a, offer_b):
        """Combine two offers into a single route.

        Args:
            offer_a (tuple): First offer (A → C).
            offer_b (tuple): Second offer (C → B).

        Returns:
            dict: Combined route data.
        """
        try:
            total_distance = (offer_a[9] or 0) + (offer_b[9] or 0)
            total_revenue = (offer_a[6] or offer_a[10] or 0) + (offer_b[6] or offer_b[10] or 0)
            return {
                "segments": [self._format_offer(offer_a), self._format_offer(offer_b)],
                "total_distance": total_distance,
                "total_revenue": total_revenue,
                "price_per_km": total_revenue / total_distance if total_distance else 0
            }
        except Exception as e:
            logging.error(f"Error combining offers: {e}")
            return {"segments": [], "total_distance": 0, "total_revenue": 0, "price_per_km": 0}

class ConcurrentModificationException(Exception):
    """Combine two offers into a single route.
    
    Raised when concurrent modifications are detected while processing routes."""
    pass