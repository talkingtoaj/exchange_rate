# exchange_rate_downloader.py

import csv
import time
from datetime import datetime

import browser_cookie3
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os


def get_user_input():
    currency_pair = input("Enter the currency pair [AUD-TRY]: ") or "aud-try"
    start_date = input("Enter the start date (YYYY-MM-DD): ") or '2024-02-13'
    return currency_pair, start_date

def construct_url(currency_pair:str) -> str:
    base_url = "https://www.investing.com/currencies/"
    return f"{base_url}{currency_pair}-historical-data"

def download_data(url:str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_html(html_content: str) -> list:
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'class': 'historicalTbl'})
    rows = table.find_all('tr')
    
    data = []
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        date = cols[0].text.strip()
        rate = cols[1].text.strip()
        data.append([date, rate])
    
    return data



def select_date_range(url, start_date, end_date):
    # Retrieve cookies from the user's Chrome browser
    cookies = browser_cookie3.chrome(domain_name='investing.com')



    # Initialize the WebDriver with options to use the user's Chrome profile
    chrome_user_data_dir = os.getenv('CHROME_USER_DATA_DIR')
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={chrome_user_data_dir}")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)

        # Add the retrieved cookies to the Selenium WebDriver
        for cookie in cookies:
            driver.add_cookie({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expiry': cookie.expires,
                'secure': cookie.secure,
                'httpOnly': cookie.has_nonstandard_attr('httponly')
            })
        driver.refresh()

        date_range_div = driver.find_element(By.CSS_SELECTOR, '.flex.flex-1.items-center.gap-3.5.rounded.border.border-solid.border-[#CFD4DA].bg-white.px-3.5.py-2.shadow-select')
        date_range_div.click()
        time.sleep(2)
        # Locate the start date input (adjust the selector as needed)
        start_date_input = driver.find_element(By.CSS_SELECTOR, 'CSS_SELECTOR_FOR_START_DATE_INPUT')
        # Enter the start date
        start_date_input.send_keys(start_date)
        # Locate the end date input (adjust the selector as needed)
        end_date_input = driver.find_element(By.CSS_SELECTOR, 'CSS_SELECTOR_FOR_END_DATE_INPUT')
        # Enter the end date
        end_date_input.send_keys(end_date)
        # Submit the date range (if needed, adjust the selector as needed)
        submit_button = driver.find_element(By.CSS_SELECTOR, 'CSS_SELECTOR_FOR_SUBMIT_BUTTON')
        submit_button.click()
        # Wait for the changes to take effect
        time.sleep(5)  # Adjust the sleep time as needed
        # Extract the HTML content of the page
        html_content = driver.page_source
        return html_content

    finally:
        # Close the browser
        driver.quit()

def save_to_csv(data, filename: str):
    # expects data to be in format: [['date', 'rate'], ['date', 'rate'], ...]
    with open(filename, 'w', newline='') as csvfile: # w flag means we are writing to a file and if it exists it will be overwritten
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Rate'])
        writer.writerows(data)

def download_by_api(start_date:str, end_date:str, currency_pair:str):
    API_KEY = os.getenv('EXCHANGE_RATES_API_KEY')
    # extract symbols to get AUD and TRY from AUD-TRY
    symbols = currency_pair.split('-')
    # url = f"https://api.exchangeratesapi.io/v1/timeseries?access_key={API_KEY}&start_date={start_date}&end_date={end_date}&base={symbols[0]}&symbols={symbols[1]}"
    # calc a list of datestamps between start_date and end_date (inclusive of start_date, but not end_date)
    date_stamp = start_date
    from datetime import datetime, timedelta
    results = []
    while date_stamp != end_date:
        date_stamp = datetime.strptime(date_stamp, "%Y-%m-%d") + timedelta(days=1)
        date_stamp = date_stamp.strftime("%Y-%m-%d")
        url = f"https://api.exchangeratesapi.io/v1/{date_stamp}?access_key={API_KEY}&symbols={symbols[0]},{symbols[1]}"
        print(url)
        response = requests.get(url)
        rate = response.json()['rates'][symbols[1].upper()]
        results.append([date_stamp, rate])
        print(results)
        save_to_csv(results, 'test.csv')
        pass
    return results



def main():
    load_dotenv()
    currency_pair, start_date = get_user_input()
    end_date = datetime.now().strftime("%Y-%m-%d")
    data = download_by_api(start_date, end_date, currency_pair)
    filename = f"{currency_pair}_exchange_rates.csv"
    save_to_csv(data, filename)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    main()