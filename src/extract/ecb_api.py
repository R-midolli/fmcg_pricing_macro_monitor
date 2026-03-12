from datetime import datetime, timedelta, timezone
from io import BytesIO
import os

import pandas as pd
import requests

def fetch_ecb_fx():
    """
    Fetches the EUR/USD exchange rate from the European Central Bank (ECB) Data Portal API.
    Identifier: EXR.D.USD.EUR.SP00.A (Daily Spot Exchange Rate)
    """
    print("Fetching ECB FX Data (EUR/USD)...")
    url = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=3 * 365)
    params = {
        "format": "csvdata",
        "startPeriod": start_date.isoformat(),
        "endPeriod": end_date.isoformat(),
    }

    headers = {"Accept": "text/csv"}

    response = requests.get(url, params=params, headers=headers, timeout=30)

    if response.status_code != 200:
        print(f"Failed to fetch ECB data: {response.status_code}")
        return pd.DataFrame()

    df = pd.read_csv(BytesIO(response.content))

    df = df[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={
        "TIME_PERIOD": "date",
        "OBS_VALUE": "fx_eur_usd"
    })
    df["date"] = pd.to_datetime(df["date"])
    df["fx_eur_usd"] = pd.to_numeric(df["fx_eur_usd"], errors="coerce")

    df = df.sort_values(by="date").dropna().drop_duplicates(subset=["date"])

    print(f"Successfully fetched {len(df)} records from ECB.")
    return df

if __name__ == "__main__":
    df = fetch_ecb_fx()
    if not df.empty:
        os.makedirs("data/raw", exist_ok=True)
        # Save as parquet
        df.to_parquet("data/raw/ecb_fx_eur_usd.parquet", index=False)
        print("Saved to data/raw/ecb_fx_eur_usd.parquet")
