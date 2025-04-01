# CargoBot

A terminal-based bot for freight logistics, helping to find and plan load routes.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install openai routingpy geopy colorama beautifulsoup4 requests


---

## Summary of Improvements
- **Database Menu**: Fully implemented with options to view raw data, view processed offers, verify recent offers, and correct offer data.
- **WhatsApp and Web Scraping**: Implemented with real parsing logic, integrated into the "Fetch new offers" option.
- **GPT API Optimization**: Added batch processing (3 emails per call) and email cleaning to reduce token usage.
- **Error Handling and Logging**: Added try-except blocks and a logging system to `cargobot.log`.
- **Unit Tests**: Expanded to cover database, WhatsApp, and web scraping functionality.
- **Documentation**: Added docstrings and a `README.md`.

## Final Steps for Your Developer
- **Test with Real Data**: Use actual emails, WhatsApp messages, and web platform data to verify functionality.
- **Adjust Web Scraping**: Update `web_scraper.py` to match the actual HTML structure of your web platform.
- **Deploy**: Set up on a server if needed, ensuring environment variables are configured.

cat cargobot.log
source super_bot_env/bin/activate
Tests: python3 -m unittest discover tests