import requests
import pandas as pd
import os
import xml.etree.ElementTree as ET

def fetch_insee_cpi():
    """
    Fetches Consumer Price Index (IPC) data from INSEE BDM SDMX API.
    Uses StructureSpecificData format.
    
    Series IDs (idbanks) - Base 2015, All households, Metropolitan France:
      - 001763852 : IPC - Ensemble (All items)
      - 001764565 : IPC - Produits alimentaires (Food products)
      - 001764217 : IPC - Pain et céréales (Bread & Cereals)
      - 001764229 : IPC - Viandes (Meat)
      - 001764241 : IPC - Lait, fromage et oeufs (Dairy, Cheese & Eggs)
      - 001764253 : IPC - Huiles et graisses (Oils & Fats)
      - 001764277 : IPC - Sucre, confiture, miel, chocolat (Sugar, Jam, Honey, Chocolate)
      - 001764289 : IPC - Café, thé, cacao (Coffee, Tea, Cocoa)
    """
    print("Fetching INSEE CPI Data (French Inflation by Food Category)...")

    series_map = {
        "001763852": "All Items",
        "001764565": "Food Products",
        "001764217": "Bread & Cereals",
        "001764229": "Meat",
        "001764241": "Dairy, Cheese & Eggs",
        "001764253": "Oils & Fats",
        "001764277": "Sugar, Jam, Honey, Chocolate",
        "001764289": "Coffee, Tea, Cocoa",
    }

    ids = "+".join(series_map.keys())
    url = f"https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/{ids}"
    params = {
        "startPeriod": "2020-01",
        "endPeriod": "2026-02",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Failed to fetch INSEE data: HTTP {response.status_code}")
        print(response.text[:500])
        return pd.DataFrame()

    # Parse the SDMX StructureSpecificData XML
    root = ET.fromstring(response.content)
    
    records = []

    # INSEE uses StructureSpecificData format where Series has IDBANK attribute
    # and Obs elements have TIME_PERIOD and OBS_VALUE as direct attributes.
    # Tags have namespace prefixes, so we iterate and match by local name.
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

        if tag == "Series":
            current_idbank = el.attrib.get("IDBANK")
            current_category = series_map.get(current_idbank, f"Unknown ({current_idbank})")

        elif tag == "Obs":
            period = el.attrib.get("TIME_PERIOD")
            value = el.attrib.get("OBS_VALUE")
            if period and value and current_idbank in series_map:
                records.append({
                    "date": period,
                    "cpi_index": float(value),
                    "category": current_category,
                    "idbank": current_idbank,
                })

    if not records:
        print("No observations found in INSEE response.")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df = df.sort_values(by=["category", "date"]).reset_index(drop=True)

    print(f"Successfully fetched {len(df)} CPI records across {df['category'].nunique()} categories.")
    return df


if __name__ == "__main__":
    df = fetch_insee_cpi()
    if not df.empty:
        os.makedirs("data/raw", exist_ok=True)
        df.to_parquet("data/raw/insee_cpi_france.parquet", index=False)
        print("Saved to data/raw/insee_cpi_france.parquet")
