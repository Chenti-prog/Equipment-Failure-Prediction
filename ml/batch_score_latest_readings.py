from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


# === DB CONFIG ===
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "efp_db"

MODEL_PATH = Path("models") / "failure_model_rf_v1.pkl"
SOURCE_MODEL_NAME = "rf_v1"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at: {path}")
    print(f"[INFO] Loading model from {path}")
    model = joblib.load(path)
    print("[INFO] Model loaded successfully.")
    return model


def get_recent_readings(engine, hours: int = 9999) -> pd.DataFrame:
    """
    Pull sensor readings from the last `hours` hours, based on max(timestamp).
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(timestamp), MAX(timestamp) FROM fact_sensor_readings"))
        min_ts, max_ts = list(result)[0]
        print(f"[INFO] MIN(timestamp) in fact_sensor_readings: {min_ts}")
        print(f"[INFO] MAX(timestamp) in fact_sensor_readings: {max_ts}")

        if max_ts is None:
            raise ValueError("No data in fact_sensor_readings to score.")

        cutoff_ts = max_ts - timedelta(hours=hours)
        print(f"[INFO] Using cutoff_ts = {cutoff_ts} (hours={hours})")

        query = """
        SELECT
            machine_id,
            timestamp,
            temperature,
            vibration,
            pressure,
            error_code,
            operating_hours,
            failed_within_24h
        FROM fact_sensor_readings
        WHERE timestamp >= %(cutoff)s
        ORDER BY timestamp ASC;
        """

        df = pd.read_sql(query, conn, params={"cutoff": cutoff_ts})

    print(f"[INFO] Retrieved {len(df)} recent rows for scoring.")
    if not df.empty:
        print("[INFO] Sample of recent readings:")
        print(df.head())
    return df


def map_bucket(score: float) -> str:
    if score < 0.3:
        return "LOW"
    elif score < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"


def score_readings(model, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("No recent readings to score (df is empty).")

    feature_cols = [
        "machine_id",
        "temperature",
        "vibration",
        "pressure",
        "operating_hours",
        "error_code",
    ]
    missing = set(feature_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required feature columns for scoring: {missing}")

    X = df[feature_cols].copy()

    print("[INFO] Running model.predict_proba on recent readings...")
    risk_scores = model.predict_proba(X)[:, 1]

    timestamp_scored = datetime.utcnow()
    buckets = [map_bucket(s) for s in risk_scores]

    scores_df = pd.DataFrame(
        {
            "machine_id": df["machine_id"].values,
            "timestamp_scored": [timestamp_scored] * len(df),
            "risk_score": risk_scores,
            "risk_bucket": buckets,
            "source_model": [SOURCE_MODEL_NAME] * len(df),
        }
    )

    print(f"[INFO] Created scores dataframe with {len(scores_df)} rows.")
    print("[INFO] Sample of scores:")
    print(scores_df.head())

    # Check for NaNs before writing
    nan_counts = scores_df.isna().sum()
    print("[INFO] NaN counts in scores_df:")
    print(nan_counts)

    return scores_df


def write_scores_to_db(engine, scores_df: pd.DataFrame):
    print(f"[INFO] Writing {len(scores_df)} rows to ml_failure_risk_scores...")
    with engine.begin() as conn:  # ensures commit
        scores_df.to_sql(
            "ml_failure_risk_scores",
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
    print("[INFO] Write to ml_failure_risk_scores complete.")


def main():
    try:
        engine = get_engine()

        # Connectivity check
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM fact_sensor_readings"))
            count = list(res)[0][0]
            print(f"[INFO] fact_sensor_readings row count: {count}")

        # Load model
        model = load_model(MODEL_PATH)

        # Get recent readings
        df_recent = get_recent_readings(engine, hours=9999)
        print(f"[INFO] Recent readings shape (raw): {df_recent.shape}")

        if df_recent.empty:
            print("[WARN] No recent readings to score. Exiting.")
            sys.exit(0)

        # KEEP ONLY LATEST READING PER MACHINE
        df_recent_sorted = df_recent.sort_values(["machine_id", "timestamp"])
        df_latest_per_machine = df_recent_sorted.groupby("machine_id", as_index=False).tail(1)

        print(f"[INFO] Latest-per-machine shape: {df_latest_per_machine.shape}")
        print("[INFO] Sample of latest-per-machine:")
        print(df_latest_per_machine.head())

        # Score ONLY these latest rows
        scores_df = score_readings(model, df_latest_per_machine)
        print(f"[INFO] Scores dataframe shape: {scores_df.shape}")

        # Write to DB
        write_scores_to_db(engine, scores_df)

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
