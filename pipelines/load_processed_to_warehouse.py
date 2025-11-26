from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# DB connection settings (from docker-compose)
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = 5433           # host port from docker-compose
DB_NAME = "efp_db"


def get_today_processed_dir(processed_base: str = "data_lake/processed") -> Path:
    """
    Build today's processed directory path:
      data_lake/processed/YYYY/MM/DD/
    """
    today = datetime.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    processed_dir = Path(processed_base) / year / month / day
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed directory does not exist: {processed_dir}")

    return processed_dir


def find_processed_file(processed_dir: Path) -> Path:
    """
    Find a single CSV in the processed_dir.
    """
    csv_files = list(processed_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in processed directory: {processed_dir}")
    return csv_files[0]


def get_engine():
    """
    Create a SQLAlchemy engine for PostgreSQL.
    """
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(url)
    return engine


def main():
    try:
        processed_dir = get_today_processed_dir()
        processed_file = find_processed_file(processed_dir)

        print(f"[INFO] Reading processed file: {processed_file}")
        df = pd.read_csv(processed_file)

        print(f"[INFO] Processed shape: {df.shape}")

        # Ensure column order / names match the DB schema (except id)
        expected_cols = [
            "machine_id",
            "timestamp",
            "temperature",
            "vibration",
            "pressure",
            "error_code",
            "operating_hours",
            "failed_within_24h",
        ]
        missing = set(expected_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing expected columns in processed data: {missing}")

        df = df[expected_cols]

        # Make sure timestamp is parsed as datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Connect to DB
        engine = get_engine()

        # Optional: quick connectivity check
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            print(f"[INFO] DB connectivity check: {list(res)[0][0]}")

        # Load into fact_sensor_readings
        print("[INFO] Loading data into fact_sensor_readings...")
        df.to_sql(
            "fact_sensor_readings",
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        print("[INFO] Load complete!")

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
