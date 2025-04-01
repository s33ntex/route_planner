import imaplib
import email
from email.header import decode_header
from gpt_api import parse_emails
from config import config
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

class EmailFetcher:
    """Fetches and processes emails using IMAP."""
    def __init__(self, db):
        """Initialize EmailFetcher with a database connection.

        Args:
            db (Database): Database instance.
        """
        self.db = db
        try:
            self.mail = imaplib.IMAP4_SSL(config["email_server"])
            self.mail.login(config["email_user"], config["email_pass"])
            self.mail.select(config["email_folder"])
        except Exception as e:
            logging.error(f"Error initializing EmailFetcher: {e}")
            raise

    def fetch_new_emails(self):
        """Fetch new email IDs.

        Returns:
            list: List of email IDs.
        """
        try:
            status, messages = self.mail.search(None, '(SINCE "1-Jan-2024")')
            if status != "OK":
                logging.warning("Failed to fetch email IDs.")
                return []
            return messages[0].split()
        except Exception as e:
            logging.error(f"Error fetching email IDs: {e}")
            return []

    def clean_email_body(self, body):
        """Clean email body by removing signatures and noise.

        Args:
            body (str): Email body text.

        Returns:
            str: Cleaned email body.
        """
        try:
            # Remove signatures and common footers
            body = re.sub(r"(Best regards|Cheers|Sent from|Confidentiality Notice).*", "", body, flags=re.DOTALL | re.IGNORECASE)
            # Remove extra whitespace
            body = re.sub(r"\s+", " ", body).strip()
            return body
        except Exception as e:
            logging.error(f"Error cleaning email body: {e}")
            return body

    def process_email(self, email_id):
        """Process a single email to extract its body.

        Args:
            email_id (str): Email ID.

        Returns:
            tuple: (cleaned body, raw body) or (None, None) if failed.
        """
        try:
            status, msg_data = self.mail.fetch(email_id, '(BODY.PEEK[])')
            if status != "OK":
                logging.warning(f"Failed to fetch email {email_id}.")
                return None, None
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = decode_header(msg.get("Subject", ""))[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            body = self._get_email_body(msg)
            cleaned_body = self.clean_email_body(f"{subject}\n\n{body}")
            return cleaned_body, f"{subject}\n\n{body}"
        except Exception as e:
            logging.error(f"Error processing email {email_id}: {e}")
            return None, None

    def fetch_and_process_emails(self, batch_size=3):
        """Fetch and process emails in batches.

        Args:
            batch_size (int): Number of emails to process per batch.

        Returns:
            tuple: (list of parsed offers, list of raw messages).
        """
        email_ids = self.fetch_new_emails()
        parsed_offers = []
        raw_messages = []
        for i in range(0, len(email_ids), batch_size):
            batch_ids = email_ids[i:i + batch_size]
            batch_bodies = []
            batch_raw = []
            for email_id in batch_ids:
                cleaned_body, raw = self.process_email(email_id)
                if cleaned_body:
                    batch_bodies.append(cleaned_body)
                    batch_raw.append(raw)
                    self.db.insert_raw_data("email", raw)
            if batch_bodies:
                parsed_batch = parse_emails(batch_bodies)
                for parsed, raw in zip(parsed_batch, batch_raw):
                    if parsed:
                        parsed["source"] = "email"
                        parsed_offers.append(parsed)
                        raw_messages.append(raw)
        return parsed_offers, raw_messages

    def _get_email_body(self, msg):
        """Extract the body from an email message.

        Args:
            msg (email.message.Message): Email message object.

        Returns:
            str: Email body text.
        """
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception as e:
            logging.error(f"Error extracting email body: {e}")
            return ""

    def disconnect(self):
        """Disconnect from the email server."""
        try:
            self.mail.logout()
        except Exception as e:
            logging.error(f"Error disconnecting from email server: {e}")