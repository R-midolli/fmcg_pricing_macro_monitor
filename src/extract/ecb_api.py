import requests
import pandas as pd
import os

def fetch_ecb_fx():
    """
    Fetches the EUR/USD exchange rate from the European Central Bank (ECB) Data Portal API.
    Identifier: EXR.D.USD.EUR.SP00.A (Daily Spot Exchange Rate)
    """
    print("Fetching ECB FX Data (EUR/USD)...")
    url = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&lastNObservations=100"
    
    # We want CSV format for easy parsing with Pandas
    headers = {"Accept": "text/csv"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Saving temporarily to process
        temp_file = "temp_ecb_fx.csv"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
            
        df = pd.read_csv(temp_file)
        
        # Keep only date (TIME_PERIOD) and the rate (OBS_VALUE)
        df = df[['TIME_PERIOD', 'OBS_VALUE']].rename(columns={
            'TIME_PERIOD': 'date',
            'OBS_VALUE': 'fx_eur_usd'
        })
        df['date'] = pd.to_datetime(df['date'])
        df['fx_eur_usd'] = pd.to_numeric(df['fx_eur_usd'], errors='coerce')
        
        # Sort and clean
        df = df.sort_values(by='date').dropna()
        
        os.remove(temp_file)
        print(f"Successfully fetched {len(df)} records from ECB.")
        return df
    else:
        print(f"Failed to fetch ECB data: {response.status_code}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_ecb_fx()
    if not df.empty:
        os.makedirs("data/raw", exist_ok=True)
        # Save as parquet
        df.to_parquet("data/raw/ecb_fx_eur_usd.parquet", index=False)
        print("Saved to data/raw/ecb_fx_eur_usd.parquet")
