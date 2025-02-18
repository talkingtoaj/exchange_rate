Create a .env file and add the following:

EXCHANGE_RATES_API_KEY1=<your-api-key>
EXCHANGE_RATES_API_KEY2=<your-api-key>
EXCHANGE_RATES_API_KEY3=<your-api-key>

API keys can be found at https://manage.exchangeratesapi.io/

Run the script with:

```
python main.py
```

The script will download the exchange rates for the currency pair and save them to a CSV file.