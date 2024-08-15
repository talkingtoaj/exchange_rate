import os
import csv
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

def save_to_csv(data, filename: str):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Rate'])
        writer.writerows(data)

def fetch_exchange_rate(date_stamp, symbols, API_KEY):
    url = f"https://api.exchangeratesapi.io/v1/{date_stamp}?access_key={API_KEY}&symbols={symbols[0]},{symbols[1]}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {date_stamp}: {response.status_code}")
        return None
    rate = response.json().get('rates', {}).get(symbols[1].upper())
    if rate is None:
        print(f"Rate not found for {date_stamp}")
        return None
    return [date_stamp, rate]

def download_by_api(start_date: str, end_date: str, currency_pair: str):
    API_KEY = os.getenv('EXCHANGE_RATES_API_KEY')
    if not API_KEY:
        raise ValueError("API key not found. Please set the 'EXCHANGE_RATES_API_KEY' environment variable.")
    
    symbols = currency_pair.split('-')
    if len(symbols) != 2:
        raise ValueError("Invalid currency pair format. Expected format 'BASE-TARGET'.")

    date_stamp = start_date
    results = []
    batch_size = 5
    batch = []

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = []
        while date_stamp != end_date:
            date_stamp_dt = datetime.strptime(date_stamp, "%Y-%m-%d")
            next_date_stamp_dt = date_stamp_dt + timedelta(days=1)
            date_stamp = next_date_stamp_dt.strftime("%Y-%m-%d")

            futures.append(executor.submit(fetch_exchange_rate, date_stamp, symbols, API_KEY))
            if len(futures) >= batch_size:
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        batch.append(result)
                results.extend(batch)
                print(f"{batch=}")
                save_to_csv(results, 'test.csv')
                futures = []
                batch = []

        # Process any remaining futures
        for future in as_completed(futures):
            result = future.result()
            if result:
                batch.append(result)
        results.extend(batch)
        save_to_csv(results, 'testF.csv')

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