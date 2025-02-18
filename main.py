import os
import csv
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Global variables for API key management
API_KEYS = []
CURRENT_KEY_INDEX = 0

def initialize_api_keys():
    global API_KEYS
    for i in range(1, 4):  # Load API keys 1 through 3
        key = os.getenv(f'EXCHANGE_RATES_API_KEY{i}')
        if key:
            API_KEYS.append(key)
    if not API_KEYS:
        raise ValueError("No API keys found. Please set at least one 'EXCHANGE_RATES_API_KEY{n}' environment variable.")

def get_next_api_key():
    global CURRENT_KEY_INDEX
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
    return API_KEYS[CURRENT_KEY_INDEX]

def save_to_csv(data, filename: str):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Rate'])
        writer.writerows(data)

def fetch_exchange_rate(date_stamp, symbols, API_KEY, max_retries=2):
    global CURRENT_KEY_INDEX
    current_attempt = 0
    while current_attempt <= max_retries:
        try:
            url = f"https://api.exchangeratesapi.io/v1/{date_stamp}?access_key={API_KEY}&symbols={symbols[0]},{symbols[1]}"
            response = requests.get(url)
            if response.status_code != 200:
                raise requests.exceptions.RequestException(f"Status code: {response.status_code}")
            
            rate1 = response.json().get('rates', {}).get(symbols[1].upper())
            base_rate = response.json().get('rates', {}).get(symbols[0].upper())
            rate = rate1 / base_rate
            if rate1 is None:
                print(f"Rate not found for {date_stamp}")
                return None
            return [date_stamp, rate]
        except Exception as e:
            print(f"Error with API key {CURRENT_KEY_INDEX + 1} for {date_stamp}: {str(e)}")
            if current_attempt < max_retries:
                new_key = get_next_api_key()
                print(f"Switching to API key {CURRENT_KEY_INDEX + 1}")
                API_KEY = new_key
                current_attempt += 1
                continue
            return None

def download_by_api(start_date: str, end_date: str, currency_pair: str):
    initialize_api_keys()  # Initialize the API keys list
    global CURRENT_KEY_INDEX
    
    symbols = currency_pair.split('-')
    print(f"{symbols=}")
    if len(symbols) != 2:
        raise ValueError("Invalid currency pair format. Expected format 'BASE-TARGET'.")

    date_stamp = start_date
    results = []
    batch_size = 5
    batch = []
    
    try:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            while date_stamp != end_date:
                date_stamp_dt = datetime.strptime(date_stamp, "%Y-%m-%d")
                next_date_stamp_dt = date_stamp_dt + timedelta(days=1)
                date_stamp = next_date_stamp_dt.strftime("%Y-%m-%d")

                futures.append(executor.submit(
                    fetch_exchange_rate, 
                    date_stamp, 
                    symbols, 
                    API_KEYS[CURRENT_KEY_INDEX]
                ))
                
                if len(futures) >= batch_size:
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            batch.append(result)
                    results.extend(batch)
                    print(f"{batch=}")
                    save_to_csv(results, f"{currency_pair}_exchange_rates_partial.csv")
                    futures = []
                    batch = []

            # Process any remaining futures
            for future in as_completed(futures):
                result = future.result()
                if result:
                    batch.append(result)
            results.extend(batch)
            save_to_csv(results, f"{currency_pair}_exchange_rates.csv")
            return results
    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        if results:  # Save any collected data before exiting
            save_to_csv(results, f"{currency_pair}_exchange_rates_error.csv")
        return results

def get_user_input():
    currency_pair = input("Enter the currency pair [AUD-TRY]: ") or "aud-try"
    start_date = input("Enter the start date (YYYY-MM-DD): ") or '2024-02-13'
    return currency_pair, start_date

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