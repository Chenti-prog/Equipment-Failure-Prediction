from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler



DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "efp_db"

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "failure_model_rf_v1.pkl"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_training_data(engine) -> pd.DataFrame:
    """
    Load labeled sensor data from fact_sensor_readings.
    We only use rows where failed_within_24h IS NOT NULL.
    """
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
    WHERE failed_within_24h IS NOT NULL;
    """
    df = pd.read_sql(query, engine)
    return df


def build_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    """
    Build a preprocessing + RandomForest pipeline.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    rf_clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", rf_clf),
        ]
    )
    return model


def train_and_evaluate(df: pd.DataFrame) -> Pipeline:
    """
    Train the model and print evaluation metrics.
    Returns the fitted pipeline.
    """
    # Target
    y = df["failed_within_24h"].astype(int)

    # Features: same as in the notebook
    feature_cols = [
        "machine_id",
        "temperature",
        "vibration",
        "pressure",
        "operating_hours",
        "error_code",
    ]
    X = df[feature_cols].copy()

    numeric_features = ["machine_id", "temperature", "vibration", "pressure", "operating_hours"]
    categorical_features = ["error_code"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"[INFO] Training set size: {X_train.shape}, Test set size: {X_test.shape}")

    model = build_pipeline(numeric_features, categorical_features)

    print("[INFO] Training model...")
    model.fit(X_train, y_train)
    print("[INFO] Model training complete.")

    # Evaluation
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    print(f"\n[METRIC] Accuracy: {acc:.4f}")

    try:
        auc = roc_auc_score(y_test, y_proba)
        print(f"[METRIC] ROC-AUC: {auc:.4f}")
    except Exception as e:
        print(f"[WARN] Could not compute ROC-AUC: {e}")

    print("\n[METRIC] Classification report:")
    print(classification_report(y_test, y_pred))

    cm = confusion_matrix(y_test, y_pred)
    print("\n[METRIC] Confusion matrix:")
    print(cm)

    return model


def save_model(model: Pipeline, path: Path):
    """
    Save the fitted pipeline to disk.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    print(f"[INFO] Saved model pipeline to: {path}")


def main():
    try:
        engine = get_engine()

        # quick connectivity check
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM fact_sensor_readings"))
            count = list(res)[0][0]
            print(f"[INFO] fact_sensor_readings row count: {count}")

        df = load_training_data(engine)
        print(f"[INFO] Loaded training data with shape: {df.shape}")

        if df.empty:
            print("[ERROR] No training data available (df is empty).", file=sys.stderr)
            sys.exit(1)

        model = train_and_evaluate(df)
        save_model(model, MODEL_PATH)

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
