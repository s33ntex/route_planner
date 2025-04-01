import sqlite3
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

class Database:
    """Manages SQLite database operations for CargoBot."""
    def __init__(self, db_path):
        """Initialize database connection and create tables.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create necessary tables if they do not exist."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY,
                name TEXT,
                country_code TEXT,
                lat REAL,
                lon REAL
            );
            CREATE TABLE IF NOT EXISTS city_aliases (
                id INTEGER PRIMARY KEY,
                alias TEXT,
                city_id INTEGER,
                FOREIGN KEY (city_id) REFERENCES cities(id)
            );
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY,
                source TEXT,
                timestamp DATETIME,
                raw_content TEXT
            );
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY,
                source TEXT,
                timestamp DATETIME,
                sender TEXT,
                loading_city_id INTEGER,
                unloading_city_id INTEGER,
                price REAL,
                lf_number TEXT,
                urgency TEXT,
                distance REAL,
                estimated_price REAL,
                additional_info TEXT,
                raw_message TEXT,
                FOREIGN KEY (loading_city_id) REFERENCES cities(id),
                FOREIGN KEY (unloading_city_id) REFERENCES cities(id)
            );
            CREATE TABLE IF NOT EXISTS unverified_offers (
                offer_id INTEGER PRIMARY KEY,
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            );
        """)
        self.conn.commit()

    def insert_raw_data(self, source, raw_content):
        """Insert raw data into the database.

        Args:
            source (str): Source of the data (e.g., 'email', 'whatsapp').
            raw_content (str): Raw content to store.

        Returns:
            int: ID of the inserted raw data.
        """
        try:
            self.cursor.execute(
                "INSERT INTO raw_data (source, timestamp, raw_content) VALUES (?, ?, ?)",
                (source, datetime.now(), raw_content)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Error inserting raw data: {e}")
            return None

    def get_raw_data(self, limit=10):
        """Retrieve raw data entries.

        Args:
            limit (int): Maximum number of entries to return.

        Returns:
            list: List of raw data entries.
        """
        try:
            self.cursor.execute("SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [{"id": row[0], "source": row[1], "timestamp": row[2], "raw_content": row[3]} for row in self.cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error retrieving raw data: {e}")
            return []

    def insert_city(self, name, country_code, lat, lon):
        """Insert a new city into the database.

        Args:
            name (str): City name.
            country_code (str): Country code (e.g., 'DE').
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            int: ID of the inserted city.
        """
        try:
            self.cursor.execute(
                "INSERT INTO cities (name, country_code, lat, lon) VALUES (?, ?, ?, ?)",
                (name, country_code, lat, lon)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Error inserting city: {e}")
            return None

    def insert_alias(self, alias, city_id):
        """Insert an alias for a city.

        Args:
            alias (str): Alternative name for the city.
            city_id (int): ID of the city this alias refers to.
        """
        try:
            self.cursor.execute(
                "INSERT INTO city_aliases (alias, city_id) VALUES (?, ?)",
                (alias, city_id)
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error inserting alias: {e}")

    def get_city_by_name(self, name):
        """Retrieve a city by its name.

        Args:
            name (str): City name.

        Returns:
            tuple: City data (id, name, country_code, lat, lon) or None.
        """
        try:
            self.cursor.execute("SELECT * FROM cities WHERE name = ?", (name,))
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error retrieving city by name: {e}")
            return None

    def get_city_by_alias(self, alias):
        """Retrieve a city by its alias.

        Args:
            alias (str): City alias.

        Returns:
            tuple: City data (id, name, country_code, lat, lon) or None.
        """
        try:
            self.cursor.execute(
                "SELECT c.* FROM cities c JOIN city_aliases ca ON c.id = ca.city_id WHERE ca.alias = ?",
                (alias,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error retrieving city by alias: {e}")
            return None

    def get_city_by_id(self, city_id):
        """Retrieve a city by its ID.

        Args:
            city_id (int): City ID.

        Returns:
            tuple: City data (id, name, country_code, lat, lon) or None.
        """
        try:
            self.cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error retrieving city by ID: {e}")
            return None

    def insert_offer(self, source, sender, loading_city_id, unloading_city_id, price=None, 
                    lf_number=None, urgency=None, distance=None, estimated_price=None, 
                    additional_info=None, raw_message=None):
        """Insert a new offer into the database.

        Args:
            source (str): Source of the offer (e.g., 'email', 'whatsapp').
            sender (str): Sender of the offer.
            loading_city_id (int): ID of the loading city.
            unloading_city_id (int): ID of the unloading city.
            price (float, optional): Price in EUR.
            lf_number (str, optional): LF number (e.g., 'LF1').
            urgency (str, optional): Urgency (e.g., 'today').
            distance (float, optional): Distance in km.
            estimated_price (float, optional): Estimated price if price is missing.
            additional_info (str, optional): Additional information.
            raw_message (str, optional): Raw message content.

        Returns:
            int: ID of the inserted offer.
        """
        try:
            self.cursor.execute(
                """INSERT INTO offers (source, timestamp, sender, loading_city_id, unloading_city_id, 
                   price, lf_number, urgency, distance, estimated_price, additional_info, raw_message) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (source, datetime.now(), sender, loading_city_id, unloading_city_id, price, 
                 lf_number, urgency, distance, estimated_price, additional_info, raw_message)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Error inserting offer: {e}")
            return None

    def get_offers_by_loading_city(self, city_id, days=7):
        """Retrieve offers by loading city within a time range.

        Args:
            city_id (int): ID of the loading city.
            days (int): Number of days to look back.

        Returns:
            list: List of offers.
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            self.cursor.execute(
                "SELECT * FROM offers WHERE loading_city_id = ? AND timestamp >= ?",
                (city_id, cutoff)
            )
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Error retrieving offers by loading city: {e}")
            return []

    def count_offers_from_city(self, city_id, days=7):
        """Count offers originating from a city within a time range.

        Args:
            city_id (int): ID of the city.
            days (int): Number of days to look back.

        Returns:
            int: Number of offers.
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            self.cursor.execute(
                "SELECT COUNT(*) FROM offers WHERE loading_city_id = ? AND timestamp >= ?",
                (city_id, cutoff)
            )
            return self.cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Error counting offers from city: {e}")
            return 0

    def get_all_offers(self, limit=10):
        """Retrieve all offers, most recent first.

        Args:
            limit (int): Maximum number of offers to return.

        Returns:
            list: List of offers.
        """
        try:
            self.cursor.execute("SELECT * FROM offers ORDER BY timestamp DESC LIMIT ?", (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Error retrieving all offers: {e}")
            return []

    def get_recent_offers(self, limit=10):
        """Retrieve recent offers.

        Args:
            limit (int): Maximum number of offers to return.

        Returns:
            list: List of recent offers.
        """
        return self.get_all_offers(limit)

    def log_unverified_offer(self, offer_id):
        """Log an offer as unverified for later correction.

        Args:
            offer_id (int): ID of the offer to log.
        """
        try:
            self.cursor.execute("INSERT OR IGNORE INTO unverified_offers (offer_id) VALUES (?)", (offer_id,))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error logging unverified offer: {e}")

    def get_unverified_offers(self):
        """Retrieve all unverified offers.

        Returns:
            list: List of unverified offers.
        """
        try:
            self.cursor.execute("SELECT o.* FROM offers o JOIN unverified_offers u ON o.id = u.offer_id")
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Error retrieving unverified offers: {e}")
            return []

    def get_offer_by_id(self, offer_id):
        """Retrieve an offer by its ID.

        Args:
            offer_id (int): ID of the offer.

        Returns:
            tuple: Offer data or None.
        """
        try:
            self.cursor.execute("SELECT * FROM offers WHERE id = ?", (offer_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error retrieving offer by ID: {e}")
            return None

    def update_offer(self, offer_id, new_loading_city, new_unloading_city, new_price):
        """Update an offer with new data.

        Args:
            offer_id (int): ID of the offer to update.
            new_loading_city (str): New loading city name.
            new_unloading_city (str): New unloading city name.
            new_price (float): New price in EUR.
        """
        try:
            # Normalize new cities
            loading_city = DataNormalizer(self).normalize_city(new_loading_city)
            unloading_city = DataNormalizer(self).normalize_city(new_unloading_city)
            if not loading_city or not unloading_city:
                logging.warning(f"Could not normalize cities for offer {offer_id}")
                return
            self.cursor.execute(
                "UPDATE offers SET loading_city_id = ?, unloading_city_id = ?, price = ? WHERE id = ?",
                (loading_city[0], unloading_city[0], float(new_price) if new_price else None, offer_id)
            )
            self.cursor.execute("DELETE FROM unverified_offers WHERE offer_id = ?", (offer_id,))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error updating offer {offer_id}: {e}")

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
        except Exception as e:
            logging.error(f"Error closing database: {e}")