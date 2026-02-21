# 🛒 European FMCG Cost Pressure Monitor

> **Real-time macro-economic analysis of cost pressures facing the French FMCG sector.**
> Built with 100% real data from public APIs.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-orange)
![Dash](https://img.shields.io/badge/Plotly_Dash-Dashboard-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🎯 Business Context

The European FMCG sector faces unprecedented cost pressures from:
- **Agricultural commodity price volatility** (Cocoa, Coffee, Wheat, Sugar)
- **EUR/USD exchange rate fluctuations** impacting import costs
- **Consumer price inflation** measured by the INSEE CPI

This dashboard monitors these forces in real time and answers:
- Are raw material costs being passed through to consumers?
- Which product categories are most exposed to commodity shocks?
- What is the "cost squeeze" gap between input costs and retail inflation?

---

## 📊 Data Sources (100% Real APIs)

| Source | Data | API |
|--------|------|-----|
| **European Central Bank** | EUR/USD daily exchange rate | [ECB Data Portal](https://data.ecb.europa.eu/) |
| **INSEE** | French Consumer Price Index by food category | [INSEE BDM SDMX](https://bdm.insee.fr/) |
| **Yahoo Finance** | Agricultural commodity prices (Cocoa, Coffee, Sugar, Wheat) | [yfinance](https://pypi.org/project/yfinance/) |
| **Open Food Facts** | FMCG product catalog (brands, categories, Nutri-Score) | [Open Food Facts API](https://world.openfoodfacts.org/) |

---

## 🏗️ Architecture

```
APIs (ECB, INSEE, Yahoo Finance, Open Food Facts)
        │
        ▼
  src/extract/          → Raw Parquet files (data/raw/)
        │
        ▼
  src/transform/        → DuckDB star schema (data/marts/)
  (build_marts.py)        dim_date, dim_product,
                          fact_commodities, fact_inflation, fact_fx
                          mart_category_pressure
        │
        ▼
  src/dashboard/        → Plotly Dash (localhost:8050)
  (app.py + pages/)       4 interactive pages
```

**Orchestration**: Apache Airflow DAG (`dags/pricing_monitor_dag.py`)
**CI/CD**: GitHub Actions (`.github/workflows/data_pipeline.yml`)

---

## 📈 Dashboard Pages

| Page | Description |
|------|-------------|
| **🌍 Macro Overview** | KPI cards + trend charts for commodities, FX, and CPI |
| **📈 Cost Shock** | YoY heatmap + bar chart highlighting commodity surges |
| **🏷️ Inflation Translation** | Interactive overlay of input costs vs consumer inflation |
| **⚠️ Category Risk** | Heatmap + data table scoring product category exposure |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### 1. Install dependencies
```bash
uv sync
```

### 2. Extract data from APIs
```bash
uv run python src/extract/ecb_api.py
uv run python src/extract/insee_api.py
uv run python src/extract/commodities_api.py
uv run python src/extract/openfoodfacts_api.py
```

### 3. Build DuckDB marts
```bash
uv run python src/transform/build_marts.py
```

### 4. Run the dashboard
```bash
uv run python src/dashboard/app.py
```
Open [http://localhost:8050](http://localhost:8050)

### 5. Run tests
```bash
uv run pytest tests/ -v
```

---

## 📁 Project Structure

```
fmcg_pricing_macro_monitor/
├── .github/workflows/     # CI pipeline
├── dags/                  # Airflow DAG
├── data/
│   ├── raw/               # Raw Parquet from APIs
│   └── marts/             # DuckDB-transformed models
├── src/
│   ├── extract/           # API extraction scripts
│   │   ├── ecb_api.py
│   │   ├── insee_api.py
│   │   ├── commodities_api.py
│   │   └── openfoodfacts_api.py
│   ├── transform/
│   │   └── build_marts.py # DuckDB star schema builder
│   └── dashboard/
│       ├── app.py         # Dash entry point
│       └── pages/         # Multi-page dashboard
├── tests/                 # pytest data quality tests
├── pyproject.toml
├── .gitignore
└── .env.example
```

---

## 🧠 Key Analytical Concepts

- **Cost Squeeze Score** = Commodity YoY % − CPI YoY %
  - Positive → Input costs rising faster than retail prices (margin compression)
  - Negative → Retailers passing costs through to consumers
- **Primary Commodity Exposure** — Maps Open Food Facts categories to raw materials
- **YoY Analysis** — All metrics computed as year-over-year percentage changes

---

## 📜 License

MIT
