import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

def fetch_commodities_data():
    """
    Fetches historical monthly data for key agricultural commodities using Yahoo Finance.
    These represent raw material costs for the FMCG industry.
    """
    print("Fetching Commodities Data from Yahoo Finance...")
    
    # Define the tickers for key commodities
    # CC=F : Cocoa
    # KC=F : Coffee
    # SB=F : Sugar
    # ZW=F : Wheat
    
    commodities = {
        'Cocoa': 'CC=F',
        'Coffee': 'KC=F',
        'Sugar': 'SB=F',
        'Wheat': 'ZW=F'
    }
    
    CENTS_TICKERS = {"KC=F", "SB=F", "ZW=F"}
    
    # We want ~3 years of data to see the recent inflation shocks
    end_date = datetime.today()
    start_date = end_date - timedelta(days=3*365)
    
    all_data = []
    
    for name, ticker in commodities.items():
        print(f"Downloading {name} ({ticker})...")
        try:
            t = yf.Ticker(ticker)
            # Use interval="1wk" to match the original download params
            df = t.history(start=start_date, end=end_date, interval="1wk", auto_adjust=True)
            
            if not df.empty:
                if ticker in CENTS_TICKERS:
                    df[["Open", "High", "Low", "Close"]] /= 100
                
                temp_df = pd.DataFrame({
                    'date': df.index,
                    'price_usd': df['Close'].values,
                    'commodity': name
                })
                all_data.append(temp_df)
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Clean up timezone and NaNs
        final_df['date'] = pd.to_datetime(final_df['date']).dt.tz_localize(None)
        final_df['date'] = final_df['date'].dt.normalize()  # strip time, keep date
        final_df = final_df.dropna(subset=['price_usd'])
        
        print(f"Successfully fetched {len(final_df)} commodity records.")
        return final_df
    
    return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_commodities_data()
    if not df.empty:
        os.makedirs("data/raw", exist_ok=True)
        df.to_parquet("data/raw/commodities_prices.parquet", index=False)
        print("Saved to data/raw/commodities_prices.parquet")
