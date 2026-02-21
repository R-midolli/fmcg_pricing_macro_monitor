"""
DuckDB transformation layer.
Reads raw Parquet files from data/raw/ and builds dimensional models + an analytics mart in data/marts/.
"""
import duckdb
import os

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
MARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "marts")


def build_marts():
    os.makedirs(MARTS_DIR, exist_ok=True)
    con = duckdb.connect()

    # ── 1. dim_date ──────────────────────────────────────────────────────
    print("Building dim_date...")
    con.execute(f"""
        COPY (
            WITH dates AS (
                SELECT DISTINCT date FROM read_parquet('{_p("insee_cpi_france.parquet")}')
                UNION
                SELECT DISTINCT date FROM read_parquet('{_p("commodities_prices.parquet")}')
            )
            SELECT
                date,
                EXTRACT(YEAR FROM date)    AS year,
                EXTRACT(MONTH FROM date)   AS month,
                EXTRACT(QUARTER FROM date) AS quarter,
                strftime(date, '%B')       AS month_name
            FROM dates
            ORDER BY date
        ) TO '{_m("dim_date.parquet")}' (FORMAT PARQUET)
    """)

    # ── 2. dim_product ───────────────────────────────────────────────────
    print("Building dim_product...")
    con.execute(f"""
        COPY (
            SELECT
                product_id,
                product_name,
                brand,
                category,
                nutriscore,
                origin_country,
                -- Flag ingredient-based commodity exposure
                CASE
                    WHEN LOWER(category) LIKE '%chocolate%'
                      OR LOWER(category) LIKE '%cacao%'
                      OR LOWER(category) LIKE '%cocoa%'       THEN 'Cocoa'
                    WHEN LOWER(category) LIKE '%coffee%'
                      OR LOWER(category) LIKE '%café%'        THEN 'Coffee'
                    WHEN LOWER(category) LIKE '%sugar%'
                      OR LOWER(category) LIKE '%sucre%'
                      OR LOWER(category) LIKE '%confiture%'
                      OR LOWER(category) LIKE '%bonbon%'
                      OR LOWER(category) LIKE '%candy%'       THEN 'Sugar'
                    WHEN LOWER(category) LIKE '%bread%'
                      OR LOWER(category) LIKE '%pain%'
                      OR LOWER(category) LIKE '%cereal%'
                      OR LOWER(category) LIKE '%céréal%'
                      OR LOWER(category) LIKE '%flour%'
                      OR LOWER(category) LIKE '%farine%'
                      OR LOWER(category) LIKE '%wheat%'
                      OR LOWER(category) LIKE '%biscuit%'     THEN 'Wheat'
                    ELSE 'Other'
                END AS primary_commodity_exposure
            FROM read_parquet('{_p("openfoodfacts_products.parquet")}')
            WHERE product_id IS NOT NULL
        ) TO '{_m("dim_product.parquet")}' (FORMAT PARQUET)
    """)

    # ── 3. fact_commodities ──────────────────────────────────────────────
    print("Building fact_commodities...")
    con.execute(f"""
        COPY (
            SELECT
                date,
                commodity,
                price_usd,
                -- YoY % change
                (price_usd - LAG(price_usd, 12) OVER (PARTITION BY commodity ORDER BY date))
                    / NULLIF(LAG(price_usd, 12) OVER (PARTITION BY commodity ORDER BY date), 0) * 100
                    AS yoy_change_pct,
                -- Rolling 3-month average
                AVG(price_usd) OVER (PARTITION BY commodity ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
                    AS rolling_3m_avg
            FROM read_parquet('{_p("commodities_prices.parquet")}')
            ORDER BY commodity, date
        ) TO '{_m("fact_commodities.parquet")}' (FORMAT PARQUET)
    """)

    # ── 4. fact_inflation ────────────────────────────────────────────────
    print("Building fact_inflation...")
    con.execute(f"""
        COPY (
            SELECT
                date,
                category,
                cpi_index,
                idbank,
                -- YoY % change in CPI
                (cpi_index - LAG(cpi_index, 12) OVER (PARTITION BY category ORDER BY date))
                    / NULLIF(LAG(cpi_index, 12) OVER (PARTITION BY category ORDER BY date), 0) * 100
                    AS yoy_inflation_pct,
                -- MoM % change
                (cpi_index - LAG(cpi_index, 1) OVER (PARTITION BY category ORDER BY date))
                    / NULLIF(LAG(cpi_index, 1) OVER (PARTITION BY category ORDER BY date), 0) * 100
                    AS mom_change_pct
            FROM read_parquet('{_p("insee_cpi_france.parquet")}')
            ORDER BY category, date
        ) TO '{_m("fact_inflation.parquet")}' (FORMAT PARQUET)
    """)

    # ── 5. fact_fx ───────────────────────────────────────────────────────
    print("Building fact_fx...")
    con.execute(f"""
        COPY (
            WITH monthly_fx AS (
                SELECT
                    DATE_TRUNC('month', date) AS date,
                    AVG(fx_eur_usd) AS fx_eur_usd
                FROM read_parquet('{_p("ecb_fx_eur_usd.parquet")}')
                GROUP BY 1
            )
            SELECT
                date,
                fx_eur_usd,
                (fx_eur_usd - LAG(fx_eur_usd, 12) OVER (ORDER BY date))
                    / NULLIF(LAG(fx_eur_usd, 12) OVER (ORDER BY date), 0) * 100
                    AS yoy_change_pct
            FROM monthly_fx
            ORDER BY date
        ) TO '{_m("fact_fx.parquet")}' (FORMAT PARQUET)
    """)

    # ── 6. mart_category_pressure ────────────────────────────────────────
    print("Building mart_category_pressure...")
    con.execute(f"""
        COPY (
            WITH commodity_latest AS (
                SELECT
                    commodity,
                    date,
                    price_usd,
                    yoy_change_pct
                FROM read_parquet('{_m("fact_commodities.parquet")}')
            ),
            inflation AS (
                SELECT
                    category AS inflation_category,
                    date,
                    cpi_index,
                    yoy_inflation_pct
                FROM read_parquet('{_m("fact_inflation.parquet")}')
            ),
            fx AS (
                SELECT date, fx_eur_usd, yoy_change_pct AS fx_yoy_pct
                FROM read_parquet('{_m("fact_fx.parquet")}')
            ),
            -- Map INSEE inflation categories to commodity names
            mapping AS (
                SELECT 'Coffee, Tea, Cocoa' AS inflation_category, 'Cocoa'  AS commodity UNION ALL
                SELECT 'Coffee, Tea, Cocoa',                        'Coffee'            UNION ALL
                SELECT 'Sugar, Jam, Honey, Chocolate',              'Sugar'             UNION ALL
                SELECT 'Sugar, Jam, Honey, Chocolate',              'Cocoa'             UNION ALL
                SELECT 'Bread & Cereals',                           'Wheat'
            )
            SELECT
                i.date,
                i.inflation_category,
                i.cpi_index,
                i.yoy_inflation_pct,
                m.commodity,
                c.price_usd       AS commodity_price_usd,
                c.yoy_change_pct  AS commodity_yoy_pct,
                f.fx_eur_usd,
                f.fx_yoy_pct,
                -- Pressure score: if commodity cost rises faster than consumer inflation
                COALESCE(c.yoy_change_pct, 0) - COALESCE(i.yoy_inflation_pct, 0) AS cost_squeeze_score
            FROM inflation i
            INNER JOIN mapping m ON i.inflation_category = m.inflation_category
            LEFT  JOIN commodity_latest c ON m.commodity = c.commodity AND i.date = c.date
            LEFT  JOIN fx f ON i.date = f.date
            WHERE c.price_usd IS NOT NULL
            ORDER BY i.date, i.inflation_category
        ) TO '{_m("mart_category_pressure.parquet")}' (FORMAT PARQUET)
    """)

    con.close()
    print("All marts built successfully!")


# ── helpers ──────────────────────────────────────────────────────────────
def _p(filename: str) -> str:
    """Return absolute path for a raw parquet file (forward-slash for DuckDB)."""
    return os.path.join(RAW_DIR, filename).replace("\\", "/")

def _m(filename: str) -> str:
    """Return absolute path for a mart parquet file (forward-slash for DuckDB)."""
    return os.path.join(MARTS_DIR, filename).replace("\\", "/")


if __name__ == "__main__":
    build_marts()
