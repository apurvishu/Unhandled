"""Script to train and save baseline ML models for development and testing."""

import os
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Output models directory
MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_freight_model():
    print("Training baseline Freight Rate ML model...")
    # Synthetic dataset
    # Features: [base_rate, current_rate, horizon_days, fuel_factor]
    np.random.seed(42)
    X = np.random.uniform(low=[15.0, 15.0, 1, 0.8], high=[35.0, 35.0, 90, 1.3], size=(500, 4))
    # Target: freight rate
    y = X[:, 1] * X[:, 3] * (1.0 + np.sin(X[:, 2] / 15.0) * 0.05) + np.random.normal(0, 0.5, 500)

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    out_path = MODELS_DIR / "freight_v1.0.joblib"
    joblib.dump(model, out_path)
    print(f"Saved freight model to {out_path}")


def train_congestion_model():
    print("Training baseline Port Congestion ML model...")
    # Features: [current_waiting, current_at_berth, berth_capacity, horizon_hours]
    np.random.seed(42)
    X = np.random.uniform(low=[0, 1, 5, 6], high=[15, 12, 15, 72], size=(500, 4))
    # Target: [waiting_time, berth_utilization]
    y_waiting = (X[:, 0] * 3.5) + (X[:, 3] * 0.2) + np.random.normal(0, 1.0, 500)
    y_util = np.clip((X[:, 1] / X[:, 2]) * 100.0 + (X[:, 3] * 0.1), 10.0, 99.0)
    y = np.column_stack([y_waiting, y_util])

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    out_path = MODELS_DIR / "congestion_v1.0.joblib"
    joblib.dump(model, out_path)
    print(f"Saved congestion model to {out_path}")


if __name__ == "__main__":
    train_freight_model()
    train_congestion_model()
    print("All mock ML models generated successfully.")
