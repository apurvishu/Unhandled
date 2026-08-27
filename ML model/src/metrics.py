"""
SIH 2026 - ML Model Evaluation
------------------------------

Evaluates:

1. Freight-rate forecasting model
2. Congestion forecasting model

Freight metrics:
- MAE
- RMSE
- R2
- MAPE
- Within +/-5%
- Within +/-10%

Congestion metrics:
- MAE
- RMSE
- R2
- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Classification Report

Expected project structure:

ML model/
│
├── data/
│   └── SIH_AI_ML_Freight_And_Congestion_Prototype_Dataset.xlsx
│
├── models/
│   ├── freight_forecasting_model.pkl
│   ├── congestion_forecasting_model.pkl
│   └── model_metadata.pkl
│
├── outputs/
│
└── src/
    ├── train_models.py
    ├── forecast.py
    ├── metrics.py
    └── predict.py
"""


# ============================================================
# IMPORTS
# ============================================================

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "SIH_AI_ML_Freight_And_Congestion_Prototype_Dataset.xlsx"
)


MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# MODEL PATHS
# ============================================================

FREIGHT_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "freight_forecasting_model.pkl"
)


CONGESTION_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "congestion_forecasting_model.pkl"
)


METADATA_PATH = os.path.join(
    MODEL_DIR,
    "model_metadata.pkl"
)


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(DATA_PATH):

    raise FileNotFoundError(
        f"\nDataset not found:\n{DATA_PATH}\n\n"
        "Place the Excel dataset inside ML model/data/"
    )


if not os.path.exists(
    FREIGHT_MODEL_PATH
):

    raise FileNotFoundError(
        f"\nFreight model not found:\n"
        f"{FREIGHT_MODEL_PATH}\n\n"
        "Run train_models.py first."
    )


if not os.path.exists(
    CONGESTION_MODEL_PATH
):

    raise FileNotFoundError(
        f"\nCongestion model not found:\n"
        f"{CONGESTION_MODEL_PATH}\n\n"
        "Run train_models.py first."
    )


if not os.path.exists(
    METADATA_PATH
):

    raise FileNotFoundError(
        f"\nModel metadata not found:\n"
        f"{METADATA_PATH}\n\n"
        "Run train_models.py first."
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("             SIH 2026 - MODEL EVALUATION")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_excel(
    DATA_PATH,
    sheet_name="Final_ML_Dataset"
)


df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)


df = df.dropna(
    subset=["date"]
).copy()


df = df.sort_values(
    [
        "route",
        "vessel_type",
        "date"
    ]
).reset_index(drop=True)


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading trained models...")

freight_model = joblib.load(
    FREIGHT_MODEL_PATH
)


congestion_model = joblib.load(
    CONGESTION_MODEL_PATH
)


metadata = joblib.load(
    METADATA_PATH
)


freight_features = metadata[
    "freight_features"
]


congestion_features = metadata[
    "congestion_features"
]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

print("Preparing features...")


# ------------------------------------------------------------
# TIME FEATURES
# ------------------------------------------------------------

df["year"] = (
    df["date"].dt.year
)


df["month"] = (
    df["date"].dt.month
)


df["day"] = (
    df["date"].dt.day
)


df["day_of_week"] = (
    df["date"].dt.dayofweek
)


df["day_of_year"] = (
    df["date"].dt.dayofyear
)


df["week_of_year"] = (
    df["date"]
    .dt.isocalendar()
    .week
    .astype(int)
)


df["quarter"] = (
    df["date"].dt.quarter
)


# ------------------------------------------------------------
# CYCLIC SEASONAL FEATURES
# ------------------------------------------------------------

df["month_sin"] = np.sin(
    2 * np.pi
    * df["month"]
    / 12
)


df["month_cos"] = np.cos(
    2 * np.pi
    * df["month"]
    / 12
)


df["day_of_year_sin"] = np.sin(
    2 * np.pi
    * df["day_of_year"]
    / 365
)


df["day_of_year_cos"] = np.cos(
    2 * np.pi
    * df["day_of_year"]
    / 365
)


# ============================================================
# FREIGHT LAG FEATURES
# ============================================================

freight_group = (
    df.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[
        "freight_rate_usd_per_mt"
    ]
)


for lag in [
    1,
    2,
    3,
    7,
    14,
    30
]:

    df[
        f"freight_lag_{lag}"
    ] = freight_group.shift(lag)


df["freight_rolling_7"] = (
    freight_group.transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .mean()
    )
)


df["freight_rolling_14"] = (
    freight_group.transform(
        lambda x:
        x.shift(1)
        .rolling(14)
        .mean()
    )
)


df["freight_rolling_30"] = (
    freight_group.transform(
        lambda x:
        x.shift(1)
        .rolling(30)
        .mean()
    )
)


df["freight_change_1d"] = (
    freight_group.pct_change(1)
)


df["freight_change_7d"] = (
    freight_group.pct_change(7)
)


df["freight_change_30d"] = (
    freight_group.pct_change(30)
)


# ============================================================
# CONGESTION LAG FEATURES
# ============================================================

congestion_group = (
    df.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[
        "congestion_index"
    ]
)


for lag in [
    1,
    2,
    3,
    7,
    14,
    30
]:

    df[
        f"congestion_lag_{lag}"
    ] = congestion_group.shift(lag)


df["congestion_rolling_7"] = (
    congestion_group.transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .mean()
    )
)


df["congestion_rolling_14"] = (
    congestion_group.transform(
        lambda x:
        x.shift(1)
        .rolling(14)
        .mean()
    )
)


df["congestion_rolling_30"] = (
    congestion_group.transform(
        lambda x:
        x.shift(1)
        .rolling(30)
        .mean()
    )


# ============================================================
# NEXT-DAY TARGETS
# ============================================================

df[
    "target_freight_next_day"
] = (
    df.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[
        "freight_rate_usd_per_mt"
    ].shift(-1)
)


df[
    "target_congestion_next_day"
] = (
    df.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[
        "congestion_index"
    ].shift(-1)
)


# ============================================================
# REMOVE ROWS WITHOUT REQUIRED HISTORY
# ============================================================

required_history = [

    "freight_lag_1",
    "freight_lag_2",
    "freight_lag_3",
    "freight_lag_7",
    "freight_lag_14",
    "freight_lag_30",

    "freight_rolling_7",
    "freight_rolling_14",
    "freight_rolling_30",

    "congestion_lag_1",
    "congestion_lag_2",
    "congestion_lag_3",
    "congestion_lag_7",
    "congestion_lag_14",
    "congestion_lag_30",

    "congestion_rolling_7",
    "congestion_rolling_14",
    "congestion_rolling_30",

    "target_freight_next_day",
    "target_congestion_next_day"
]


df = df.dropna(
    subset=required_history
).copy()


# ============================================================
# TIME-BASED TEST SPLIT
# ============================================================

unique_dates = (
    df["date"]
    .sort_values()
    .unique()
)


split_index = int(
    len(unique_dates) * 0.80
)


split_date = (
    unique_dates[
        split_index
    ]
)


test_df = df[
    df["date"] >= split_date
].copy()


print(
    "\nTest period:"
)

print(
    test_df["date"].min(),
    "→",
    test_df["date"].max()
)


# ============================================================
# FREIGHT PREDICTIONS
# ============================================================

print(
    "\nGenerating freight predictions..."
)


actual_freight = (
    test_df[
        "target_freight_next_day"
    ]
)


predicted_freight = (
    freight_model.predict(
        test_df[
            freight_features
        ]
    )
)


# ============================================================
# FREIGHT METRICS
# ============================================================

freight_mae = (
    mean_absolute_error(
        actual_freight,
        predicted_freight
    )
)


freight_rmse = np.sqrt(
    mean_squared_error(
        actual_freight,
        predicted_freight
    )
)


freight_r2 = (
    r2_score(
        actual_freight,
        predicted_freight
    )
)


freight_mape = (
    mean_absolute_percentage_error(
        actual_freight,
        predicted_freight
    )
    * 100
)


# Within tolerance
percentage_error = (
    np.abs(
        predicted_freight
        -
        actual_freight
    )
    /
    np.abs(actual_freight)
) * 100


freight_within_5 = (
    percentage_error <= 5
).mean() * 100


freight_within_10 = (
    percentage_error <= 10
).mean() * 100


# ============================================================
# PRINT FREIGHT RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("                 FREIGHT MODEL")
print("=" * 70)

print(
    f"MAE                 : "
    f"{freight_mae:.4f}"
)

print(
    f"RMSE                : "
    f"{freight_rmse:.4f}"
)

print(
    f"R2                  : "
    f"{freight_r2:.4f}"
)

print(
    f"MAPE                : "
    f"{freight_mape:.2f}%"
)

print(
    f"Within +/-5%        : "
    f"{freight_within_5:.2f}%"
)

print(
    f"Within +/-10%       : "
    f"{freight_within_10:.2f}%"
)


# ============================================================
# CONGESTION PREDICTIONS
# ============================================================

print(
    "\nGenerating congestion predictions..."
)


actual_congestion = (
    test_df[
        "target_congestion_next_day"
    ]
)


predicted_congestion = (
    congestion_model.predict(
        test_df[
            congestion_features
        ]
    )
)


# Keep the continuous prediction in valid range
predicted_congestion = np.clip(
    predicted_congestion,
    0,
    100
)


# ============================================================
# CONGESTION REGRESSION METRICS
# ============================================================

congestion_mae = (
    mean_absolute_error(
        actual_congestion,
        predicted_congestion
    )
)


congestion_rmse = np.sqrt(
    mean_squared_error(
        actual_congestion,
        predicted_congestion
    )
)


congestion_r2 = (
    r2_score(
        actual_congestion,
        predicted_congestion
    )
)


print("\n")
print("=" * 70)
print("               CONGESTION REGRESSION")
print("=" * 70)

print(
    f"MAE                 : "
    f"{congestion_mae:.4f}"
)

print(
    f"RMSE                : "
    f"{congestion_rmse:.4f}"
)

print(
    f"R2                  : "
    f"{congestion_r2:.4f}"
)


# ============================================================
# CONVERT CONGESTION INDEX TO CLASSES
# ============================================================

def congestion_class(
    value
):

    if value <= 30:
        return "LOW"

    elif value <= 60:
        return "MEDIUM"

    return "HIGH"


actual_classes = (
    actual_congestion
    .apply(
        congestion_class
    )
)


predicted_classes = (
    pd.Series(
        predicted_congestion,
        index=test_df.index
    )
    .apply(
        congestion_class
    )
)


# ============================================================
# CLASSIFICATION METRICS
# ============================================================

labels = [
    "LOW",
    "MEDIUM",
    "HIGH"
]


congestion_accuracy = (
    accuracy_score(
        actual_classes,
        predicted_classes
    )
)


congestion_precision = (
    precision_score(
        actual_classes,
        predicted_classes,
        labels=labels,
        average="weighted",
        zero_division=0
    )
)


congestion_recall = (
    recall_score(
        actual_classes,
        predicted_classes,
        labels=labels,
        average="weighted",
        zero_division=0
    )
)


congestion_f1 = (
    f1_score(
        actual_classes,
        predicted_classes,
        labels=labels,
        average="weighted",
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    actual_classes,
    predicted_classes,
    labels=labels
)


# ============================================================
# PRINT CLASSIFICATION RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("             CONGESTION CLASSIFICATION")
print("=" * 70)

print(
    f"Accuracy             : "
    f"{congestion_accuracy:.4f}"
)

print(
    f"Precision            : "
    f"{congestion_precision:.4f}"
)

print(
    f"Recall               : "
    f"{congestion_recall:.4f}"
)

print(
    f"F1 Score             : "
    f"{congestion_f1:.4f}"
)


print(
    "\nConfusion Matrix:"
)

print(
    pd.DataFrame(
        cm,
        index=[
            "Actual LOW",
            "Actual MEDIUM",
            "Actual HIGH"
        ],
        columns=[
            "Pred LOW",
            "Pred MEDIUM",
            "Pred HIGH"
        ]
    )
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print(
    "\nClassification Report:"
)

print(
    classification_report(
        actual_classes,
        predicted_classes,
        labels=labels,
        zero_division=0
    )
)


# ============================================================
# SAVE PREDICTIONS
# ============================================================

prediction_results = test_df[
    [
        "date",
        "route",
        "vessel_type"
    ]
].copy()


prediction_results[
    "actual_freight"
] = actual_freight.values


prediction_results[
    "predicted_freight"
] = predicted_freight


prediction_results[
    "actual_congestion"
] = actual_congestion.values


prediction_results[
    "predicted_congestion"
] = predicted_congestion


prediction_results[
    "actual_congestion_class"
] = actual_classes.values


prediction_results[
    "predicted_congestion_class"
] = predicted_classes.values


prediction_results.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "model_predictions.csv"
    ),
    index=False
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics = pd.DataFrame({

    "Model": [

        "Freight",
        "Freight",
        "Freight",
        "Freight",
        "Freight",
        "Freight",

        "Congestion",
        "Congestion",
        "Congestion",
        "Congestion",
        "Congestion",
        "Congestion",
        "Congestion"
    ],

    "Metric": [

        "MAE",
        "RMSE",
        "R2",
        "MAPE",
        "Within +/-5%",
        "Within +/-10%",

        "MAE",
        "RMSE",
        "R2",
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score"
    ],

    "Value": [

        freight_mae,
        freight_rmse,
        freight_r2,
        freight_mape,
        freight_within_5,
        freight_within_10,

        congestion_mae,
        congestion_rmse,
        congestion_r2,
        congestion_accuracy,
        congestion_precision,
        congestion_recall,
        congestion_f1
    ]
})


metrics.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "model_evaluation_metrics.csv"
    ),
    index=False
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

cm_df = pd.DataFrame(
    cm,
    index=[
        "Actual LOW",
        "Actual MEDIUM",
        "Actual HIGH"
    ],
    columns=[
        "Predicted LOW",
        "Predicted MEDIUM",
        "Predicted HIGH"
    ]
)


cm_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "congestion_confusion_matrix.csv"
    )
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n")
print("=" * 70)
print("                 EVALUATION COMPLETE")
print("=" * 70)

print(
    "\nSaved:"
)

print(
    os.path.join(
        OUTPUT_DIR,
        "model_evaluation_metrics.csv"
    )
)

print(
    os.path.join(
        OUTPUT_DIR,
        "model_predictions.csv"
    )
)

print(
    os.path.join(
        OUTPUT_DIR,
        "congestion_confusion_matrix.csv"
    )
)
