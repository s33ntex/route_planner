import logging
from database import Database
from email_fetcher import EmailFetcher
from whatsapp_parser import process_whatsapp_file
from web_scraper import scrape_web_platform
from data_normalizer import DataNormalizer
from route_planner import RoutePlanner
from risk_assessor import RiskAssessor
from ui import display_menu, display_offer, display_route, display_database_menu
from config import config
from colorama import Fore, Style

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

def main():
    """Main function to run the CargoBot application."""
    try:
        db = Database(config["db_path"])
        normalizer = DataNormalizer(db)
        planner = RoutePlanner(db)
        assessor = RiskAssessor(db)
        fetcher = EmailFetcher(db)

        while True:
            choice = display_menu()
            if choice == "0":
                fetcher.disconnect()
                db.close()
                logging.info("CargoBot exited successfully.")
                break
            elif choice == "1":
                city = input("Enter current city: ")
                city_data = normalizer.normalize_city(city)
                if city_data:
                    offers = planner.find_single_load_anywhere(city_data[0])
                    for offer in offers:
                        display_offer(offer, db)
                else:
                    print(f"{Fore.RED}City not found!{Style.RESET_ALL}")
            elif choice == "2":
                start = input("Enter start city: ")
                end = input("Enter destination city: ")
                start_data = normalizer.normalize_city(start)
                end_data = normalizer.normalize_city(end)
                if start_data and end_data:
                    routes = planner.find_single_load_a_to_b(start_data[0], end_data[0])
                    for route in routes:
                        display_route({"segments": route if isinstance(route, list) else [route], 
                                       "total_distance": sum(r["distance"] or 0 for r in (route if isinstance(route, list) else [route])), 
                                       "total_revenue": sum(r["price"] or r["estimated_price"] or 0 for r in (route if isinstance(route, list) else [route]))}, db)
                else:
                    print(f"{Fore.RED}One or both cities not found!{Style.RESET_ALL}")
            elif choice == "3":
                city = input("Enter starting city: ")
                city_data = normalizer.normalize_city(city)
                if city_data:
                    route = planner.find_multi_leg_route(city_data[0])
                    display_route(route, db)
                    if route and route["segments"]:
                        risk = assessor.assess_return_load_risk(route["segments"][-1]["unloading_city_id"])
                        print(f"Return load risk: {risk}")
                else:
                    print(f"{Fore.RED}City not found!{Style.RESET_ALL}")
            elif choice == "4":
                city = input("Enter city: ")
                city_data = normalizer.normalize_city(city)
                if city_data:
                    offers = db.get_offers_by_loading_city(city_data[0], days=5)
                    for offer in offers:
                        display_offer(planner._format_offer(offer), db)
                else:
                    print(f"{Fore.RED}City not found!{Style.RESET_ALL}")
            elif choice == "5":
                # Fetch email offers
                parsed_offers, raw_messages = fetcher.fetch_and_process_emails()
                for parsed_data, raw in zip(parsed_offers, raw_messages):
                    if parsed_data and parsed_data.get("loading_city") and parsed_data.get("unloading_city"):
                        offer = normalizer.process_offer(parsed_data, raw)
                        if offer:
                            offer_id = db.insert_offer(**offer)
                            if offer_id:
                                print(f"Added email offer: {offer['sender']} - {db.get_city_by_id(offer['loading_city_id'])[1]} → {db.get_city_by_id(offer['unloading_city_id'])[1]}")
                    else:
                        print(f"Skipped email: Missing loading/unloading city")

                # Fetch WhatsApp offers
                whatsapp_offers = process_whatsapp_file(config["whatsapp_export_path"])
                for offer_data in whatsapp_offers:
                    offer = normalizer.process_offer(offer_data)
                    if offer:
                        offer_id = db.insert_offer(**offer)
                        if offer_id:
                            print(f"Added WhatsApp offer: {offer['sender']} - {db.get_city_by_id(offer['loading_city_id'])[1]} → {db.get_city_by_id(offer['unloading_city_id'])[1]}")
                            db.insert_raw_data("whatsapp", str(offer_data))

                # Fetch web offers
                web_offers = scrape_web_platform(config["web_platform_url"])
                for offer_data in web_offers:
                    offer = normalizer.process_offer(offer_data)
                    if offer:
                        offer_id = db.insert_offer(**offer)
                        if offer_id:
                            print(f"Added web offer: {offer['sender']} - {db.get_city_by_id(offer['loading_city_id'])[1]} → {db.get_city_by_id(offer['unloading_city_id'])[1]}")
                            db.insert_raw_data("web", str(offer_data))
            elif choice == "6":
                while True:
                    db_choice = display_database_menu()
                    if db_choice == "0":
                        break
                    elif db_choice == "1":
                        raw_data = db.get_raw_data()
                        if raw_data:
                            for entry in raw_data:
                                print(f"Source: {entry['source']}, Timestamp: {entry['timestamp']}")
                                print(f"Raw Content: {entry['raw_content']}\n")
                        else:
                            print("No raw data found.")
                    elif db_choice == "2":
                        offers = db.get_all_offers()
                        if offers:
                            for offer in offers:
                                formatted_offer = planner._format_offer(offer)
                                display_offer(formatted_offer, db)
                        else:
                            print("No processed offers found.")
                    elif db_choice == "3":
                        recent_offers = db.get_recent_offers()
                        if recent_offers:
                            for offer in recent_offers:
                                formatted_offer = planner._format_offer(offer)
                                display_offer(formatted_offer, db)
                                verdict = input("Is this offer correct? (y/n): ").lower()
                                if verdict == "n":
                                    db.log_unverified_offer(offer[0])
                                    print("Offer marked for correction.")
                        else:
                            print("No recent offers found.")
                    elif db_choice == "4":
                        offer_id = input("Enter offer ID to correct (or 'list' to see unverified offers): ")
                        if offer_id.lower() == "list":
                            unverified = db.get_unverified_offers()
                            if unverified:
                                for offer in unverified:
                                    formatted_offer = planner._format_offer(offer)
                                    display_offer(formatted_offer, db)
                            else:
                                print("No unverified offers found.")
                            offer_id = input("Enter offer ID to correct: ")
                        offer = db.get_offer_by_id(offer_id)
                        if offer:
                            formatted_offer = planner._format_offer(offer)
                            display_offer(formatted_offer, db)
                            new_loading = input(f"New loading city (current: {db.get_city_by_id(offer[4])[1]}): ") or db.get_city_by_id(offer[4])[1]
                            new_unloading = input(f"New unloading city (current: {db.get_city_by_id(offer[5])[1]}): ") or db.get_city_by_id(offer[5])[1]
                            new_price = input(f"New price (current: {offer[6]}): ") or offer[6]
                            db.update_offer(offer_id, new_loading, new_unloading, new_price)
                            print("Offer updated successfully.")
                        else:
                            print("Offer not found.")
                    else:
                        print("Invalid choice. Please try again.")
            else:
                print("Invalid choice. Please try again.")
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        print(f"{Fore.RED}An unexpected error occurred. Check cargobot.log for details.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()