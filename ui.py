from colorama import init, Fore, Style
import logging

init()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

def display_menu():
    """Display the main menu.

    Returns:
        str: User's menu choice.
    """
    print("\n=== CargoBot Menu ===")
    print("1. Find best load from CURRENT CITY")
    print("2. Plan route from CURRENT CITY to DESTINATION")
    print("3. Build multi-leg route from CURRENT CITY")
    print("4. Check past 5 days of historical offers for CURRENT CITY")
    print("5. Fetch new offers")
    print("6. Database Menu")
    print("0. Exit")
    return input("Enter your choice (0-6): ")

def display_database_menu():
    """Display the database menu.

    Returns:
        str: User's database menu choice.
    """
    print("\n=== Database Menu ===")
    print("1. View raw data")
    print("2. View processed offers")
    print("3. Verify recent offers")
    print("4. Correct offer data")
    print("0. Back to main menu")
    return input("Enter your choice (0-4): ")

def display_offer(offer, db):
    """Display a single offer in a formatted way.

    Args:
        offer (dict): Offer data.
        db (Database): Database instance for city lookups.
    """
    try:
        loading_city = db.get_city_by_id(offer["loading_city_id"])[1]
        unloading_city = db.get_city_by_id(offer["unloading_city_id"])[1]
        price = offer["price"] or offer["estimated_price"]
        distance = offer["distance"]
        price_per_km = offer["price_per_km"]
        color = Fore.GREEN if price_per_km and price_per_km >= 2.0 else Fore.YELLOW if price_per_km and price_per_km >= 1.5 else Fore.RED
        print(f"{color}{loading_city} → {unloading_city}", end=" ")
        if distance:
            print(f"({distance:.1f} km)", end=" ")
        if price:
            print(f"- {price}€", end=" ")
        if price_per_km:
            print(f"({price_per_km:.2f} €/km)", end=" ")
        if offer["lf_number"]:
            print(f"LF: {offer['lf_number']}", end=" ")
        if offer["urgency"]:
            print(f"Urgency: {offer['urgency']}", end=" ")
        if offer["additional_info"]:
            print(f"Info: {offer['additional_info']}", end="")
        print(f"{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"Error displaying offer: {e}")
        print(f"{Fore.RED}Error displaying offer.{Style.RESET_ALL}")

def display_route(route, db):
    """Display a route with all segments.

    Args:
        route (dict): Route data with segments.
        db (Database): Database instance for city lookups.
    """
    try:
        if not route or not route["segments"]:
            print(f"{Fore.YELLOW}No route found!{Style.RESET_ALL}")
            return
        total_price_per_km = route["total_revenue"] / route["total_distance"] if route["total_distance"] else 0
        color = Fore.GREEN if total_price_per_km >= 2.0 else Fore.YELLOW if total_price_per_km >= 1.5 else Fore.RED
        print(f"\n{color}Total: {route['total_distance']:.1f} km, {route['total_revenue']}€ "
              f"({total_price_per_km:.2f} €/km){Style.RESET_ALL}")
        for seg in route["segments"]:
            display_offer(seg, db)
    except Exception as e:
        logging.error(f"Error displaying route: {e}")
        print(f"{Fore.RED}Error displaying route.{Style.RESET_ALL}")