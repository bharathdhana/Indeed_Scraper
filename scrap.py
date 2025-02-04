import os
import time
import random
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
    return element.get_text(strip=True) if element else default


def random_sleep(min_sleep=3, max_sleep=6):
    """Generates random sleep time to avoid detection."""
    time.sleep(random.uniform(min_sleep, max_sleep))


def create_driver():
    """Creates a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    try:
        return webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        print(f"Error creating WebDriver: {e}")
        return None


def get_page_source(url, driver):
    """Gets the page source using Selenium."""
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon")))
        time.sleep(2)  # Allow additional time for dynamic content
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

    for job_card in soup.select("div.job_seen_beacon"):
        try:
            title = get_element_text(job_card.find('h2', class_='jobTitle'))
            company = get_element_text(job_card.find('span', class_='css-1h7lukg eu4oa1w0'))
            location = get_element_text(job_card.find('div', class_='company_location css-i375s1 e37uo190'))
            job_url = "https://in.indeed.com" + job_card.find('a', class_='jcs-JobTitle')['href'] if job_card.find('a', class_='jcs-JobTitle') else 'N/A'

            job_data = {'Title': title, 'Company': company, 'Location': location, 'Job URL': job_url}
            jobs.append(job_data)
        except Exception as e:
            print(f"Error scraping job card: {e}")
            continue

    print(f"Found {len(jobs)} jobs on this page.")
    return jobs


def save_data(data, filename, file_format, output_dir='output'):
    """Saves the results to CSV, Excel, or JSON."""
    df = pd.DataFrame(data)
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    try:
        if file_format == 'csv':
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif file_format == 'json':
            df.to_json(filepath, orient='records', lines=True, force_ascii=False)
        elif file_format == 'excel':
            df.to_excel(filepath if filepath.endswith('.xlsx') else filepath + '.xlsx', index=False, engine='openpyxl')
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

    driver = create_driver()
    if not driver:
        return  # Exit if driver creation fails

    try:
        for page in range(num_pages):
            url = f"{base_url}&start={page * 10}"
            print(f"Scraping page {page + 1}...")

            page_source = get_page_source(url, driver)
            if page_source:
                all_jobs.extend(scrape_jobs(page_source))
                random_sleep()
            else:
                print(f"Skipping page {page + 1} due to loading issues.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

    if all_jobs:
        file_format = input("Enter file format to save (csv, json, excel): ").strip().lower()

        if file_format not in {"csv", "json", "excel"}:
            print("Invalid file format! Please enter csv, json, or excel.")
        else:
            filename = f"indeed_jobs.{file_format if file_format != 'excel' else 'xlsx'}"

            save_data(all_jobs, filename, file_format)
            print(f"Saved {len(all_jobs)} jobs to {filename}")
    else:
        print("No jobs found to save.")


if __name__ == "__main__":
    main()
