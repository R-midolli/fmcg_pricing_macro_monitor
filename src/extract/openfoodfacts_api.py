import requests
import pandas as pd
import os

def fetch_open_food_facts(country="france", page_size=250):
    """
    Fetches a selection of products from Open Food Facts API to act as our product dimension.
    We will filter for beverages, snacks, dairy to simulate FMCG.
    """
    print(f"Fetching Open Food Facts Data for {country}...")
    
    # We use the search API
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    
    params = {
        "search_terms": "",
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
        "sort_by": "popularity_key",
        "countries_tags_en": country
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        
        extracted_data = []
        for p in products:
            extracted_data.append({
                "product_id": p.get("_id"),
                "product_name": p.get("product_name"),
                "brand": p.get("brands"),
                "category": p.get("categories"),
                "nutriscore": p.get("nutriscore_grade"),
                "origin_country": p.get("origins", "Unknown")
            })
            
        df = pd.DataFrame(extracted_data)
        
        # Clean up some messy categories/brands (just take the first one)
        df['brand'] = df['brand'].str.split(',').str[0].str.strip()
        df['category'] = df['category'].str.split(',').str[0].str.strip()
        df['nutriscore'] = df['nutriscore'].str.upper()
        
        # Drop rows where we lack basic info
        df = df.dropna(subset=['product_name', 'brand'])
        
        print(f"Successfully fetched {len(df)} products.")
        return df
    else:
        print(f"Failed to fetch Open Food Facts data: {response.status_code}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_open_food_facts(page_size=500)
    if not df.empty:
        os.makedirs("data/raw", exist_ok=True)
        df.to_parquet("data/raw/openfoodfacts_products.parquet", index=False)
        print("Saved to data/raw/openfoodfacts_products.parquet")
