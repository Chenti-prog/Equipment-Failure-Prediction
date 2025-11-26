-- init.sql
-- This script runs automatically when the Postgres container is first created.
-- It assumes the database efp_db already exists (created via POSTGRES_DB).

-- Create machines dimension table
CREATE TABLE IF NOT EXISTS dim_machines (
    machine_id      INT PRIMARY KEY,
    location        TEXT NOT NULL,
    model           TEXT NOT NULL,
    install_date    DATE NOT NULL
);

-- Create sensor readings fact table
CREATE TABLE IF NOT EXISTS fact_sensor_readings (
    id               SERIAL PRIMARY KEY,
    machine_id       INT NOT NULL REFERENCES dim_machines(machine_id),
    timestamp        TIMESTAMPTZ NOT NULL,
    temperature      DOUBLE PRECISION NOT NULL,
    vibration        DOUBLE PRECISION NOT NULL,
    pressure         DOUBLE PRECISION NOT NULL,
    error_code       TEXT NOT NULL,
    operating_hours  DOUBLE PRECISION NOT NULL,
    failed_within_24h INT,  -- 0/1 label, can be NULL for unlabeled future data
    UNIQUE (machine_id, timestamp)  -- prevent duplicate readings
);

-- Create ML scores table
CREATE TABLE IF NOT EXISTS ml_failure_risk_scores (
    id               SERIAL PRIMARY KEY,
    machine_id       INT NOT NULL REFERENCES dim_machines(machine_id),
    timestamp_scored TIMESTAMPTZ NOT NULL,
    risk_score       DOUBLE PRECISION NOT NULL,  -- probability 0-1
    risk_bucket      TEXT NOT NULL,              -- LOW / MEDIUM / HIGH
    source_model     TEXT DEFAULT 'rf_v1',       -- simple version tag
    UNIQUE (machine_id, timestamp_scored, source_model)
);
