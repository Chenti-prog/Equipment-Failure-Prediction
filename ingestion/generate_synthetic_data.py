import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def create_raw_directory(base_dir: str = "data_lake/raw") -> Path:
    """
    Create a date-partitioned directory like data_lake/raw/YYYY/MM/DD
    and return the Path object.
    """
    today = datetime.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    raw_path = Path(base_dir) / year / month / day
    raw_path.mkdir(parents=True, exist_ok=True)
    return raw_path


def simulate_sensor_data(
    num_machines: int = 5,
    readings_per_machine: int = 200,
    start_time: datetime | None = None,
) -> pd.DataFrame:
    """
    Simulate sensor readings for a set of machines.
    Each machine gets `readings_per_machine` rows.
    """
    if start_time is None:
        # start 2 days ago to allow some "future within 24h" failures
        start_time = datetime.now() - timedelta(days=2)

    machine_ids = list(range(1, num_machines + 1))

    records: list[dict] = []

    for machine_id in machine_ids:
        # randomize base installation operating hours a bit
        base_operating_hours = random.uniform(1000, 5000)

        current_time = start_time

        for i in range(readings_per_machine):
            # advance time by ~30 minutes per reading
            current_time += timedelta(minutes=30)

            # baseline values
            temperature = np.random.normal(loc=70, scale=10)  # °C
            vibration = np.random.normal(loc=1.5, scale=0.5)  # m/s^2
            pressure = np.random.normal(loc=5, scale=1.0)     # bar

            # occasionally simulate bad conditions
            if random.random() < 0.15:
                temperature += np.random.uniform(15, 30)   # spikes
                vibration += np.random.uniform(1.0, 3.0)
                pressure += np.random.uniform(1.0, 3.0)

            # operating hours increases with time
            operating_hours = base_operating_hours + (i * 0.5)  # +0.5h per reading

            # derive error_code based on conditions
            if temperature > 100 or vibration > 3.5 or pressure > 8:
                error_code = random.choice(["WARN", "ERR1", "ERR2"])
            else:
                error_code = "OK"

            # heuristic for failure label:
            # high temp + high vibration + non-OK error → high failure risk
            risk_score = 0.0
            if temperature > 95:
                risk_score += 0.4
            if vibration > 3.0:
                risk_score += 0.3
            if pressure > 7.5:
                risk_score += 0.2
            if error_code != "OK":
                risk_score += 0.2

            # bound the risk between 0 and 1
            risk_score = min(risk_score, 1.0)

            # convert risk_score → probability of failing within 24h
            # then sample a label
            failure_probability = risk_score * 0.8  # dampen it a bit
            failed_within_24h = int(random.random() < failure_probability)

            records.append(
                {
                    "machine_id": machine_id,
                    "timestamp": current_time.isoformat(),
                    "temperature": round(float(temperature), 2),
                    "vibration": round(float(vibration), 3),
                    "pressure": round(float(pressure), 2),
                    "error_code": error_code,
                    "operating_hours": round(float(operating_hours), 1),
                    "failed_within_24h": failed_within_24h,
                }
            )

    df = pd.DataFrame(records)
    return df


def main():
    # 1) Decide where to write
    raw_dir = create_raw_directory()

    # 2) Generate synthetic data
    df = simulate_sensor_data(
        num_machines=5,
        readings_per_machine=200,  # total 1000 rows
    )

    # 3) Build filename with today's date
    today_str = datetime.today().strftime("%Y-%m-%d")
    filename = f"equipment_readings_{today_str}.csv"
    filepath = raw_dir / filename

    # 4) Save to CSV
    df.to_csv(filepath, index=False)
    print(f"Generated synthetic sensor data: {filepath}")
    print(f"Rows: {len(df)}")
    print("Sample:")
    print(df.head())


if __name__ == "__main__":
    main()
