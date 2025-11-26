from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def get_today_paths(
    raw_base: str = "data_lake/raw",
    processed_base: str = "data_lake/processed",
) -> tuple[Path, Path]:
    """
    Build today's raw and processed directory paths:
      raw:        data_lake/raw/YYYY/MM/DD/
      processed:  data_lake/processed/YYYY/MM/DD/
    """
    today = datetime.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    raw_dir = Path(raw_base) / year / month / day
    processed_dir = Path(processed_base) / year / month / day
    processed_dir.mkdir(parents=True, exist_ok=True)

    return raw_dir, processed_dir


def find_raw_file(raw_dir: Path) -> Path:
    """
    Find a single CSV in the raw_dir. If there are multiple,
    just take the first one for now.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in raw directory: {raw_dir}")

    # For now we just grab the first; could be extended to choose latest by name.
    return csv_files[0]


def clean_sensor_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the raw sensor dataframe.
    - Convert dtypes
    - Drop obviously bad rows
    - Handle missing values
    """
    # Ensure expected columns exist
    expected_cols = {
        "machine_id",
        "timestamp",
        "temperature",
        "vibration",
        "pressure",
        "error_code",
        "operating_hours",
        "failed_within_24h",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns in raw data: {missing}")

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Numeric conversions
    numeric_cols = ["machine_id", "temperature", "vibration", "pressure", "operating_hours", "failed_within_24h"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Basic cleaning: drop rows with null in critical fields
    df = df.dropna(
        subset=["machine_id", "timestamp", "temperature", "vibration", "pressure", "operating_hours"]
    )

    # Fill missing labels (if any) with 0 for now (non-failure)
    df["failed_within_24h"] = df["failed_within_24h"].fillna(0).astype(int)

    # Fill missing error codes with "OK"
    df["error_code"] = df["error_code"].fillna("OK").astype(str)

    # Remove obviously impossible values (simple sanity checks)
    df = df[
        (df["temperature"].between(-20, 200))
        & (df["vibration"].between(0, 20))
        & (df["pressure"].between(0, 50))
        & (df["operating_hours"] >= 0)
    ]

    # Optional: sort by machine_id, timestamp
    df = df.sort_values(by=["machine_id", "timestamp"]).reset_index(drop=True)

    return df


def main():
    try:
        raw_dir, processed_dir = get_today_paths()
        raw_file = find_raw_file(raw_dir)

        print(f"[INFO] Reading raw file: {raw_file}")
        df_raw = pd.read_csv(raw_file)

        print(f"[INFO] Raw shape: {df_raw.shape}")
        df_clean = clean_sensor_dataframe(df_raw)
        print(f"[INFO] Cleaned shape: {df_clean.shape}")

        # Build processed file name
        today_str = datetime.today().strftime("%Y-%m-%d")
        processed_file = processed_dir / f"equipment_readings_clean_{today_str}.csv"

        df_clean.to_csv(processed_file, index=False)
        print(f"[INFO] Saved processed data to: {processed_file}")

        # Show a small sample
        print("[INFO] Sample of cleaned data:")
        print(df_clean.head())

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
