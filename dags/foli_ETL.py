from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

def fetch_and_load_data():
    import psycopg2
    from psycopg2.extras import execute_values
    load_dotenv()
    # --- Postgres connection (plain psycopg2) ---
    conn = psycopg2.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DOCKER_DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )
    cur = conn.cursor()

    try:
        # --- Create table ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                polled_at TIMESTAMP,
                service_date DATE,
                vehicleref TEXT,
                lineref TEXT,
                delaysecs INTEGER,
                inpanic BOOLEAN,
                incongestion BOOLEAN,
                next_stop TEXT,
                bus_name TEXT
            );
        """)
        conn.commit()

        # --- Fetch API ---
        url = "https://data.foli.fi/siri/vm"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        vehicles = data["result"]["vehicles"]
        poll_time = datetime.utcnow()

        rows = []
        for k, v in vehicles.items():
            rows.append((
                poll_time,
                poll_time.date(),
                str(v.get("vehicleref", k)),
                str(v.get("lineref")),
                v.get("delaysecs"),
                bool(v.get("inpanic")) if v.get("inpanic") is not None else None,
                bool(v.get("incongestion")) if v.get("incongestion") is not None else None,
                v.get("next_stoppointname"),
                v.get("next_destinationdisplay"),
            ))

        if rows:
            sql = """
                INSERT INTO vehicles (
                    polled_at, service_date, vehicleref, lineref,
                    delaysecs, inpanic, incongestion, next_stop, bus_name
                ) VALUES %s
            """
            execute_values(cur, sql, rows)
            conn.commit()
            print(f"Inserted {len(rows)} rows")

    finally:
        cur.close()
        conn.close()

with DAG(
    dag_id="foli_bus_ingestion_3min",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="*/3 * * * *",
    catchup=False,
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_and_load_task",
        python_callable=fetch_and_load_data,
    )
