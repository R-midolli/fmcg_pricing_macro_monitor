"""
Lightweight Airflow DAG for the FMCG Cost Pressure Monitor pipeline.
Schedule: Weekly (every Monday at 06:00 UTC).

Tasks:
  1. Extract data from all 4 real APIs
  2. Build DuckDB dimensional models and marts
  3. Run data quality tests
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-analyst",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="fmcg_cost_pressure_monitor",
    default_args=default_args,
    description="Weekly pipeline: Extract macro data → Build DuckDB marts → Validate",
    schedule_interval="0 6 * * 1",  # Every Monday 06:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["fmcg", "macro", "pricing"],
)


# ── Task functions ───────────────────────────────────────────────────────
def extract_ecb():
    from src.extract.ecb_api import fetch_ecb_fx
    import os
    df = fetch_ecb_fx()
    os.makedirs("data/raw", exist_ok=True)
    df.to_parquet("data/raw/ecb_fx_eur_usd.parquet", index=False)

def extract_insee():
    from src.extract.insee_api import fetch_insee_cpi
    import os
    df = fetch_insee_cpi()
    os.makedirs("data/raw", exist_ok=True)
    df.to_parquet("data/raw/insee_cpi_france.parquet", index=False)

def extract_commodities():
    from src.extract.commodities_api import fetch_commodities_data
    import os
    df = fetch_commodities_data()
    os.makedirs("data/raw", exist_ok=True)
    df.to_parquet("data/raw/commodities_prices.parquet", index=False)

def extract_openfoodfacts():
    from src.extract.openfoodfacts_api import fetch_open_food_facts
    import os
    df = fetch_open_food_facts(page_size=500)
    os.makedirs("data/raw", exist_ok=True)
    df.to_parquet("data/raw/openfoodfacts_products.parquet", index=False)

def transform():
    from src.transform.build_marts import build_marts
    build_marts()

def run_tests():
    import subprocess
    result = subprocess.run(["pytest", "tests/", "-v", "--tb=short"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Data quality tests failed:\n{result.stderr}")


# ── DAG Tasks ────────────────────────────────────────────────────────────
t_ecb   = PythonOperator(task_id="extract_ecb_fx",        python_callable=extract_ecb,          dag=dag)
t_insee = PythonOperator(task_id="extract_insee_cpi",     python_callable=extract_insee,        dag=dag)
t_comm  = PythonOperator(task_id="extract_commodities",   python_callable=extract_commodities,  dag=dag)
t_off   = PythonOperator(task_id="extract_openfoodfacts", python_callable=extract_openfoodfacts, dag=dag)
t_build = PythonOperator(task_id="build_duckdb_marts",    python_callable=transform,            dag=dag)
t_test  = PythonOperator(task_id="data_quality_tests",    python_callable=run_tests,            dag=dag)

# Extraction tasks run in parallel, then transform, then test
[t_ecb, t_insee, t_comm, t_off] >> t_build >> t_test
