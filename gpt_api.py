import openai
import json
from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cargobot.log"), logging.StreamHandler()]
)

openai.api_key = config["gpt_api_key"]

def parse_emails(email_bodies):
    """Parse multiple email bodies using GPT-4o Mini.

    Args:
        email_bodies (list): List of email bodies to parse.

    Returns:
        list: List of parsed offer data.
    """
    prompt = """
    Extract the following information from each email below, separated by '---':
    - Sender's email
    - Loading city (required)
    - Unloading city (required)
    - Price (in EUR) (optional)
    - LF Number (e.g., LF1 to LF10) (optional)
    - Urgency (e.g., "today", "tomorrow", or specific date) (optional)
    - Additional info (optional)

    If loading or unloading city is missing, return null for that email.

    Emails:
    """
    prompt += "\n---\n".join(email_bodies)
    prompt += "\n\nProvide the output in JSON format as a list of objects."
    try:
        response = openai.Completion.create(
            model="gpt-4o-mini",
            prompt=prompt,
            max_tokens=1000,
            temperature=0
        )
        return json.loads(response.choices[0].text.strip())
    except Exception as e:
        logging.error(f"Error parsing emails with GPT-4o Mini: {e}")
        return []