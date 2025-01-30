#Indeed_Scraper

An Indeed scraper is a tool that automatically extracts job listings from Indeed.com. 
It gathers details like job title, company name, location, salary, and job description. 

#Requirements
1. Python 
2. Selenium
3. BeautifulSoup 
4. WebDriver for Chrome or Firefox
   

#Usage 
1. Clone the Repository.
2. Install the required packages.

   pip install requests beautifulsoup4 pandas selenium fake-useragent openpyxl
   
4. Download the appropriate webdriver for your browser and place it in your path, or specify its location in the script.
5. Edit the scrap.py script to include the URL of the Amazon page you want to scrape.
6. Run the Script.

    python scrap.py
   
8. Output of the script will generate a CSV (or) EXCEL (or) JSON file containing the extracted data. 
