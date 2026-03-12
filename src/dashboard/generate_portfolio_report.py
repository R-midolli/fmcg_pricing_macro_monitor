"""
Exports the FMCG project data into a clean JSON file
for native Plotly.js embedding in the portfolio website.
"""
import pandas as pd
import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
MARTS = os.path.join(DATA_DIR, "marts")


def _safe_float(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def _safe_date(series):
    if series.empty:
        return None
    return pd.to_datetime(series.max()).strftime("%Y-%m-%d")


def _build_summary(latest_comm, latest_inf, pressure, fx_sorted, momentum):
    latest_pressure = (
        pressure.dropna(subset=["cost_squeeze_score"])
        .sort_values("date")
        .groupby(["inflation_category", "commodity"], as_index=False)
        .last()
    )

    top_pressure = None
    top_relief = None
    if not latest_pressure.empty:
        top_pressure_row = latest_pressure.sort_values("cost_squeeze_score", ascending=False).iloc[0]
        top_pressure = {
            "commodity": top_pressure_row["commodity"],
            "category": top_pressure_row["inflation_category"],
            "score": _safe_float(top_pressure_row["cost_squeeze_score"]),
            "commodity_yoy_pct": _safe_float(top_pressure_row["commodity_yoy_pct"]),
            "inflation_yoy_pct": _safe_float(top_pressure_row["yoy_inflation_pct"]),
        }

        relief_rows = latest_pressure[latest_pressure["cost_squeeze_score"] < 0]
        if not relief_rows.empty:
            relief_row = relief_rows.sort_values("cost_squeeze_score").iloc[0]
            top_relief = {
                "commodity": relief_row["commodity"],
                "category": relief_row["inflation_category"],
                "score": _safe_float(relief_row["cost_squeeze_score"]),
                "commodity_yoy_pct": _safe_float(relief_row["commodity_yoy_pct"]),
                "inflation_yoy_pct": _safe_float(relief_row["yoy_inflation_pct"]),
            }

    comm_regime = None
    if not latest_comm.empty:
        leader_row = latest_comm.sort_values("yoy_change_pct", ascending=False).iloc[0]
        laggard_row = latest_comm.sort_values("yoy_change_pct", ascending=True).iloc[0]
        comm_regime = {
            "leader": leader_row["commodity"],
            "leader_yoy_pct": _safe_float(leader_row["yoy_change_pct"]),
            "laggard": laggard_row["commodity"],
            "laggard_yoy_pct": _safe_float(laggard_row["yoy_change_pct"]),
        }

    fx_context = None
    if len(fx_sorted) > 0:
        latest_fx = fx_sorted.iloc[-1]
        compare_idx = max(len(fx_sorted) - 4, 0)
        base_fx = fx_sorted.iloc[compare_idx]["fx_eur_usd"]
        fx_change_3m = None
        if base_fx and len(fx_sorted) >= 4:
            fx_change_3m = ((latest_fx["fx_eur_usd"] - base_fx) / base_fx) * 100
        fx_context = {
            "latest": _safe_float(latest_fx["fx_eur_usd"]),
            "change_3m_pct": _safe_float(fx_change_3m),
        }

    momentum_summary = None
    if momentum is not None and not momentum.empty:
        latest_momentum = momentum.sort_values("date").groupby("commodity", as_index=False).last()
        leader_row = latest_momentum.sort_values("change_12w_pct", ascending=False).iloc[0]
        laggard_row = latest_momentum.sort_values("change_12w_pct", ascending=True).iloc[0]
        momentum_summary = {
            "leader": leader_row["commodity"],
            "leader_change_4w_pct": _safe_float(leader_row["change_4w_pct"]),
            "leader_change_12w_pct": _safe_float(leader_row["change_12w_pct"]),
            "laggard": laggard_row["commodity"],
            "laggard_change_4w_pct": _safe_float(laggard_row["change_4w_pct"]),
            "laggard_change_12w_pct": _safe_float(laggard_row["change_12w_pct"]),
        }

    coverage = {
        "commodities_as_of": _safe_date(latest_comm["date"]) if not latest_comm.empty else None,
        "inflation_as_of": _safe_date(latest_inf["date"]) if not latest_inf.empty else None,
        "fx_as_of": _safe_date(fx_sorted["date"]),
        "fx_points": int(len(fx_sorted)),
    }

    return {
        "top_pressure": top_pressure,
        "top_relief": top_relief,
        "commodity_regime": comm_regime,
        "fx_context": fx_context,
        "momentum": momentum_summary,
        "coverage": coverage,
    }


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

    summary = _build_summary(latest_comm, latest_inf, pressure, fx_sorted, momentum)

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
        "metadata": {
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources": summary["coverage"]
        },
        "kpis": {
            "fx_eur_usd": kpi_fx,
            "cocoa_usd_t": kpis.get("Cocoa", 0),
            "coffee_usd_lb": kpis.get("Coffee", 0),
            "wheat_usd_bu": kpis.get("Wheat", 0)
        },
        "summary": {
            "top_pressure": summary["top_pressure"],
            "top_relief": summary["top_relief"],
            "commodity_regime": summary["commodity_regime"],
            "fx_context": summary["fx_context"],
            "momentum": summary["momentum"]
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

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "dashboard_fmcg_data.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
        
    print(f"Native Dashboard JSON exported to: {os.path.abspath(out_file)}")

if __name__ == "__main__":
    build_portfolio_data()
