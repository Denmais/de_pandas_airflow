from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# Intentionally incomplete.
# Goal: orchestrate extraction/cleaning/loading and make the pipeline idempotent.

def load_customers():
    raise NotImplementedError

def load_orders():
    raise NotImplementedError

def load_events():
    raise NotImplementedError

def build_daily_mart():
    raise NotImplementedError

def run_data_quality_checks():
    raise NotImplementedError

with DAG(
    dag_id="de_marketplace_daily",
    start_date=datetime(2026, 7, 1),
    schedule="@daily",
    catchup=True,
    max_active_runs=1,
    default_args={"retries": 2},
    tags=["practice", "pandas", "postgres"],
) as dag:

    start = EmptyOperator(task_id="start")

    customers = PythonOperator(
        task_id="load_customers",
        python_callable=load_customers,
    )

    orders = PythonOperator(
        task_id="load_orders",
        python_callable=load_orders,
    )

    events = PythonOperator(
        task_id="load_events",
        python_callable=load_events,
    )

    mart = PythonOperator(
        task_id="build_daily_mart",
        python_callable=build_daily_mart,
    )

    quality = PythonOperator(
        task_id="run_data_quality_checks",
        python_callable=run_data_quality_checks,
    )

    finish = EmptyOperator(task_id="finish")

    # TODO: define dependencies.
