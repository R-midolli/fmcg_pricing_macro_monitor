"""
Tests for the FMCG Cost Pressure Monitor data pipeline.
Validates raw data extraction outputs and mart transformations.
"""
import os
import pandas as pd
import pytest

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
MARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "marts")


class TestRawDataExtraction:
    """Validate that raw parquet files exist and have expected structure."""

    def test_ecb_fx_data_exists(self):
        path = os.path.join(RAW_DIR, "ecb_fx_eur_usd.parquet")
        assert os.path.exists(path), "ECB FX data file missing"
        df = pd.read_parquet(path)
        assert len(df) > 0, "ECB FX data is empty"
        assert "date" in df.columns
        assert "fx_eur_usd" in df.columns
        assert df["fx_eur_usd"].min() > 0, "FX rate should be positive"

    def test_commodities_data_exists(self):
        path = os.path.join(RAW_DIR, "commodities_prices.parquet")
        assert os.path.exists(path), "Commodities data file missing"
        df = pd.read_parquet(path)
        assert len(df) > 0, "Commodities data is empty"
        assert set(["Cocoa", "Coffee", "Sugar", "Wheat"]).issubset(set(df["commodity"].unique())), \
            "Missing expected commodities"
        assert df["price_usd"].min() > 0, "Commodity prices should be positive"

    def test_insee_cpi_data_exists(self):
        path = os.path.join(RAW_DIR, "insee_cpi_france.parquet")
        assert os.path.exists(path), "INSEE CPI data file missing"
        df = pd.read_parquet(path)
        assert len(df) > 0, "INSEE CPI data is empty"
        assert df["category"].nunique() >= 5, "Should have at least 5 CPI categories"
        assert df["cpi_index"].min() > 0, "CPI index values should be positive"

    def test_openfoodfacts_data_exists(self):
        path = os.path.join(RAW_DIR, "openfoodfacts_products.parquet")
        assert os.path.exists(path), "Open Food Facts data file missing"
        df = pd.read_parquet(path)
        assert len(df) > 0, "Product catalog is empty"
        assert "product_name" in df.columns
        assert "brand" in df.columns


class TestMarts:
    """Validate DuckDB-transformed marts."""

    def test_dim_date(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "dim_date.parquet"))
        assert len(df) > 0
        assert "year" in df.columns
        assert "month" in df.columns
        assert df["date"].is_monotonic_increasing, "dim_date should be sorted"

    def test_dim_product(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "dim_product.parquet"))
        assert len(df) > 0
        assert "primary_commodity_exposure" in df.columns
        valid_exposures = {"Cocoa", "Coffee", "Sugar", "Wheat", "Other"}
        assert set(df["primary_commodity_exposure"].unique()).issubset(valid_exposures)

    def test_fact_commodities_has_metrics(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "fact_commodities.parquet"))
        assert len(df) > 0
        assert "wow_change_pct" in df.columns
        assert "yoy_change_pct" in df.columns
        assert "rolling_13w_avg" in df.columns

    def test_mart_momentum(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "mart_momentum.parquet"))
        assert len(df) > 0
        assert "change_4w_pct" in df.columns
        assert "change_12w_pct" in df.columns

    def test_fact_inflation_has_yoy(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "fact_inflation.parquet"))
        assert len(df) > 0
        assert "yoy_inflation_pct" in df.columns

    def test_mart_category_pressure(self):
        df = pd.read_parquet(os.path.join(MARTS_DIR, "mart_category_pressure.parquet"))
        assert len(df) > 0
        assert "cost_squeeze_score" in df.columns
        assert "inflation_category" in df.columns
        assert "commodity" in df.columns
