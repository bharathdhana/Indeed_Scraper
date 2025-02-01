import os
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


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
        date_str = date_str.lower()
        if "just posted" in date_str or "today" in date_str:
            return datetime.now().strftime("%Y-%m-%d")
        elif "yesterday" in date_str:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "days ago" in date_str:
            days_ago = int(date_str.split()[0])
            return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        else:
            return datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return None


def random_sleep(min_sleep=3, max_sleep=6):
    """Generates random sleep time to avoid detection."""
    sleep_time = random.uniform(min_sleep, max_sleep)
    print(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)


def create_driver():
    """Creates a Selenium WebDriver instance."""
    chrome_options = Options()
    # Run in headless mode for production
    # chrome_options.add_argument("--headless")  # Disable for debugging
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        print(f"Error creating WebDriver: {e}")
        return None


def get_page_source(url, driver):
    """Gets the page source using Selenium."""
    try:
        driver.get(url)
        # Wait for the job cards to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
        )
        time.sleep(5)  # Allow additional time for dynamic content to load
        return driver.page_source
    except TimeoutException:
        print(f"Timed out waiting for page to load: {url}")
        return None
    except Exception as e:
        print(f"Error occurred while getting page source: {e}")
        return None


def scrape_jobs(page_source):
    """Scrapes job listings from a page."""
    soup = BeautifulSoup(page_source, 'html.parser')
    jobs = []

    job_cards = soup.select("div.job_seen_beacon")

    if not job_cards:
        print("No job cards found on this page.")
        return jobs

    for job_card in job_cards:
        try:
            # Extract job title
            title_element = job_card.find('h2', class_='jobTitle')
            title = get_element_text(title_element)

            # Extract company name
            company_element = job_card.find('span', class_='css-1h7lukg eu4oa1w0')
            company = get_element_text(company_element)

            # Extract location
            location_element = job_card.find('div', class_='company_location css-i375s1 e37uo190')
            location = get_element_text(location_element)

            # Extract date posted
            date_element = job_card.find('span', class_='heading6 error-text tapItem-gutter')
            date_posted_str = get_element_text(date_element)
            date_posted = standardize_date(date_posted_str)

            # Extract job URL
            link_element = job_card.find('a', class_='jcs-JobTitle')
            job_url = "https://in.indeed.com" + link_element['href'] if link_element and 'href' in link_element.attrs else 'N/A'

            # Print extracted data for debugging
            print(f"Title: {title}")
            print(f"Company: {company}")
            print(f"Location: {location}")
            print(f"Date Posted: {date_posted}")
            print(f"Link: {job_url}")
            print("-" * 50)

            # Add job data to the list
            job_data = {
                'Title': title,
                'Company': company,
                'Location': location,
                'Date Posted': date_posted,
                'Job URL': job_url
            }
            jobs.append(job_data)
        except Exception as e:
            print(f"Error scraping job card: {e}")
            continue

    print(f"Found {len(jobs)} jobs on this page.")
    return jobs


def save_data(data, filename, file_format, output_dir='output'):
    """Saves the results to CSV, Excel, or JSON."""
    df = pd.DataFrame(data)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filepath = os.path.join(output_dir, filename)

    try:
        if file_format == 'csv':
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif file_format == 'json':
            df.to_json(filepath, orient='records', lines=True, force_ascii=False)
        elif file_format == 'excel':
            if not filepath.endswith('.xlsx'):
                filepath += '.xlsx'
            df.to_excel(filepath, index=False, engine='openpyxl')
        print(f"Data saved to {filepath}")
    except Exception as e:
        print(f"Error saving data: {e}")


def main():
    """Main function to execute the scraper."""
    search_query = input("Enter job: ").strip()
    location = input("Enter location: ").strip()
    num_pages = int(input("Enter number of pages to scrape: ").strip())

    base_url = f'https://in.indeed.com/jobs?q={search_query}&l={location}'
    all_jobs = []

    driver = None
    try:
        driver = create_driver()
        if driver is None:
            return  # Exit if driver creation fails

        for page in range(num_pages):
            url = f"{base_url}&start={page * 10}"
            print(f"Scraping page {page + 1}...")

            page_source = get_page_source(url, driver)

            if page_source:
                jobs = scrape_jobs(page_source)
                all_jobs.extend(jobs)
                random_sleep()
            else:
                print(f"Skipping page {page + 1} due to loading issues.")
                continue

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit()

    if all_jobs:
        file_format = input("Enter file format to save (csv, json, excel): ").strip().lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"indeed_jobs_{timestamp}.{file_format}" if file_format != 'excel' else f"indeed_jobs_{timestamp}.xlsx"
        save_data(all_jobs, filename, file_format)
        print(f"Saved {len(all_jobs)} jobs to {filename}")
    else:
        print("No jobs found to save.")


if __name__ == "__main__":
    main()