import time
import random
from datetime import datetime
import pandas as pd


def get_element_text(element, default="N/A"):
    """Safely extracts text from a BeautifulSoup element."""
    if element:
        return element.get_text(strip=True)
    return default


def standardize_date(date_str):
    """Standardizes date to YYYY-MM-DD format, handles relative dates."""
    if date_str == "N/A":
        return None

    try:
        if "ago" in date_str.lower():
            date_str = date_str.replace("+", "")
            parts = date_str.lower().split(" ")
            if parts[0].isdigit():
                days_ago = int(parts[0])
                return (datetime.now() - pd.Timedelta(days=days_ago)).strftime("%Y-%m-%d")
            else:
                return datetime.now().strftime("%Y-%m-%d")
        else:
            return datetime.strptime(date_str, '%a %b %d, %Y').strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return None


def random_sleep(min_sleep=3, max_sleep=6):
    """Generates random sleep time to avoid detection."""
    sleep_time = random.uniform(min_sleep, max_sleep)
    print(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)