"""
Exports the FMCG project data into a clean JSON file
for native Plotly.js embedding in the portfolio website.
"""
import pandas as pd
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
MARTS = os.path.join(DATA_DIR, "marts")


def build_portfolio_data():
    commodities = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))
    fx = pd.read_parquet(os.path.join(MARTS, "fact_fx.parquet"))
    inflation = pd.read_parquet(os.path.join(MARTS, "fact_inflation.parquet"))
    pressure = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))

    commodities["date"] = pd.to_datetime(commodities["date"])
    fx["date"] = pd.to_datetime(fx["date"])
    inflation["date"] = pd.to_datetime(inflation["date"])

    # Try loading momentum (may not exist on first run)
    momentum_path = os.path.join(MARTS, "mart_momentum.parquet")
    momentum = pd.read_parquet(momentum_path) if os.path.exists(momentum_path) else None
    if momentum is not None:
        momentum["date"] = pd.to_datetime(momentum["date"])

    # FX Data
    fx_sorted = fx.sort_values("date")
    kpi_fx = float(fx_sorted.iloc[-1]["fx_eur_usd"]) if len(fx_sorted) > 0 else 0.0
    fx_dates = fx_sorted["date"].dt.strftime("%Y-%m-%d").tolist()
    fx_values = fx_sorted["fx_eur_usd"].tolist()

    # Commodities Data — resample weekly to monthly for the base‑100 chart
    comm_data = {}
    kpis = {}
    for c in ["Cocoa", "Coffee", "Sugar", "Wheat"]:
        d = commodities[commodities["commodity"] == c].sort_values("date")
        if len(d) > 0:
            kpis[c] = float(d.iloc[-1]["price_usd"])
            # Resample to month-end (last observation per month) for the base‑100 chart
            d_monthly = d.set_index("date").resample("MS").last().dropna(subset=["price_usd"]).reset_index()
            comm_data[c] = {
                "dates": d_monthly["date"].dt.strftime("%Y-%m-%d").tolist(),
                "prices": d_monthly["price_usd"].tolist()
            }

    # YoY Commodity Change
    latest_comm = commodities.dropna(subset=["yoy_change_pct"]).sort_values("date")
    latest_comm = latest_comm.groupby("commodity").last().reset_index()
    latest_comm = latest_comm.sort_values("yoy_change_pct", ascending=True)

    # YoY Inflation Change
    latest_inf = inflation.dropna(subset=["yoy_inflation_pct"]).sort_values("date")
    latest_inf = latest_inf.groupby("category").last().reset_index()
    latest_inf = latest_inf.sort_values("yoy_inflation_pct", ascending=True)

    # Cost Squeeze Matrix
    pivot = pressure.pivot_table(index="inflation_category", columns="commodity",
                                 values="cost_squeeze_score", aggfunc="mean").fillna(0)
    
    # Inflation Time Series (YoY % per category over time)
    inf_timeseries = {}
    for cat in inflation["category"].dropna().unique():
        d = inflation[inflation["category"] == cat].sort_values("date")
        d = d.dropna(subset=["yoy_inflation_pct"])
        if len(d) > 0:
            inf_timeseries[cat] = {
                "dates": d["date"].dt.strftime("%Y-%m-%d").tolist(),
                "values": d["yoy_inflation_pct"].tolist()
            }

    # Momentum data (last 16 weeks per commodity)
    momentum_data = {}
    if momentum is not None and not momentum.empty:
        for c in ["Cocoa", "Coffee", "Sugar", "Wheat"]:
            d = momentum[momentum["commodity"] == c].sort_values("date")
            if len(d) > 0:
                momentum_data[c] = {
                    "dates": d["date"].dt.strftime("%Y-%m-%d").tolist(),
                    "prices": d["price_usd"].tolist(),
                    "wow_pct": [round(v, 2) if pd.notna(v) else None for v in d["wow_change_pct"]],
                    "change_4w": round(float(d.iloc[-1].get("change_4w_pct", 0) or 0), 1),
                    "change_12w": round(float(d.iloc[-1].get("change_12w_pct", 0) or 0), 1),
                }

    # Final Payload
    payload = {
        "kpis": {
            "fx_eur_usd": kpi_fx,
            "cocoa_usd_t": kpis.get("Cocoa", 0),
            "coffee_usd_lb": kpis.get("Coffee", 0),
            "wheat_usd_bu": kpis.get("Wheat", 0)
        },
        "charts": {
            "commodities": comm_data,
            "fx": {
                "dates": fx_dates,
                "values": fx_values
            },
            "yoy_commodity": {
                "labels": latest_comm["commodity"].tolist(),
                "values": latest_comm["yoy_change_pct"].tolist()
            },
            "yoy_inflation": {
                "labels": latest_inf["category"].tolist(),
                "values": latest_inf["yoy_inflation_pct"].tolist()
            },
            "inflation_timeseries": inf_timeseries,
            "squeeze_matrix": {
                "x_labels": pivot.columns.tolist(),
                "y_labels": pivot.index.tolist(),
                "z_values": pivot.values.tolist()
            },
            "momentum": momentum_data
        }
    }

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "portfolio_rafael_midolli", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "dashboard_fmcg_data.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(',', ':'))
        
    print(f"Native Dashboard JSON exported to: {os.path.abspath(out_file)}")

if __name__ == "__main__":
    build_portfolio_data()
