"""
SIH 2026 - AI/ML Forecasting
--------------------------------
This script trains:

1. Freight-rate forecasting model
2. Port congestion forecasting model

Models:
- XGBoost Regression

Forecast target:
- Next-day freight rate
- Next-day congestion index

The trained models are saved in:
ML model/models/

Evaluation metrics:
- MAE
- RMSE
- R2
- MAPE (Freight)

Dataset expected at:
ML model/data/SIH_AI_ML_Freight_And_Congestion_Prototype_Dataset.xlsx
"""

import os
import warnings
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)


warnings.filterwarnings("ignore")


# ============================================================
# 1. PATH CONFIGURATION
# ============================================================

# train_models.py is inside:
# ML model/src/
#
# Dataset will be inside:
# ML model/data/
#
# Models will be inside:
# ML model/models/

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
    MODEL_DIR,
    exist_ok=True
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("=" * 70)
print("       SIH 2026 - AI/ML MODEL TRAINING")
print("=" * 70)

print("\nLoading dataset...")

if not os.path.exists(DATA_PATH):

    raise FileNotFoundError(
        "\nDataset not found.\n"
        f"Expected location:\n{DATA_PATH}\n\n"
        "Please place the Excel dataset inside:\n"
        "ML model/data/"
    )


df = pd.read_excel(
    DATA_PATH,
    sheet_name="Final_ML_Dataset"
)


print(
    f"Dataset loaded successfully."
)

print(
    f"Rows    : {df.shape[0]}"
)

print(
    f"Columns : {df.shape[1]}"
)


# ============================================================
# 3. BASIC CLEANING
# ============================================================

print("\nPreparing data...")

# Convert date
df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

# Remove rows with invalid dates
df = df.dropna(
    subset=["date"]
).copy()

# Sort chronologically
df = df.sort_values(
    [
        "route",
        "vessel_type",
        "date"
    ]
).reset_index(drop=True)


# ============================================================
# 4. CREATE TIME FEATURES
# ============================================================

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


# ============================================================
# 5. SEASONAL / CYCLIC FEATURES
# ============================================================

df["month_sin"] = np.sin(
    2 * np.pi * df["month"] / 12
)

df["month_cos"] = np.cos(
    2 * np.pi * df["month"] / 12
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
# 6. CREATE HISTORICAL FREIGHT FEATURES
# ============================================================

print(
    "\nCreating freight historical features..."
)

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


# Lag values
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


# Rolling averages
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


# ============================================================
# 7. CREATE FREIGHT TREND FEATURES
# ============================================================

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
# 8. CREATE HISTORICAL CONGESTION FEATURES
# ============================================================

print(
    "Creating congestion historical features..."
)

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


# Lag values
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


# Rolling averages
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
)


# ============================================================
# 9. CREATE NEXT-DAY TARGETS
# ============================================================

print(
    "Creating prediction targets..."
)

df["target_freight_next_day"] = (
    df.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[
        "freight_rate_usd_per_mt"
    ].shift(-1)
)

df["target_congestion_next_day"] = (
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
# 10. DEFINE FEATURES
# ============================================================

categorical_features = [

    "route",
    "origin",
    "destination",
    "vessel_type"
]


numeric_features = [

    # Vessel
    "dwt_mt",
    "loa_m",
    "beam_m",
    "draft_m",

    # Route
    "distance_nm",

    # Market
    "fuel_price_index",
    "commodity_price_index",

    # Weather
    "weather_severity",
    "wind_speed_ms",
    "wave_height_m",

    # AIS
    "vessel_density",
    "approaching_vessels",
    "avg_speed_knots",

    # Port
    "port_calls_7d",
    "median_time_in_port_days",
    "avg_dwt_mt",
    "berth_utilization_pct",
    "avg_waiting_time_hr",

    # Current state
    "freight_rate_usd_per_mt",
    "congestion_index",

    # Time
    "year",
    "month",
    "day",
    "day_of_week",
    "day_of_year",
    "week_of_year",
    "quarter",

    # Cyclic time
    "month_sin",
    "month_cos",
    "day_of_year_sin",
    "day_of_year_cos"
]


freight_history_features = [

    "freight_lag_1",
    "freight_lag_2",
    "freight_lag_3",
    "freight_lag_7",
    "freight_lag_14",
    "freight_lag_30",

    "freight_rolling_7",
    "freight_rolling_14",
    "freight_rolling_30",

    "freight_change_1d",
    "freight_change_7d",
    "freight_change_30d"
]


congestion_history_features = [

    "congestion_lag_1",
    "congestion_lag_2",
    "congestion_lag_3",
    "congestion_lag_7",
    "congestion_lag_14",
    "congestion_lag_30",

    "congestion_rolling_7",
    "congestion_rolling_14",
    "congestion_rolling_30",

]


# ============================================================
# 11. FINAL FEATURE SETS
# ============================================================

freight_features = (
    categorical_features
    +
    numeric_features
    +
    freight_history_features
)


congestion_features = (
    categorical_features
    +
    numeric_features
    +
    congestion_history_features
)


# ============================================================
# 12. REMOVE ROWS WITHOUT REQUIRED HISTORY
# ============================================================

required_columns = (
    freight_history_features
    +
    congestion_history_features
    +
    [
        "target_freight_next_day",
        "target_congestion_next_day"
    ]
)


df_model = df.dropna(
    subset=required_columns
).copy()


print(
    "\nTraining-ready rows:",
    len(df_model)
)


# ============================================================
# 13. TIME-BASED TRAIN / TEST SPLIT
# ============================================================

print(
    "\nCreating time-based train/test split..."
)

unique_dates = (
    df_model["date"]
    .sort_values()
    .unique()
)


split_index = int(
    len(unique_dates) * 0.80
)


split_date = unique_dates[
    split_index
]


train_df = df_model[
    df_model["date"] < split_date
].copy()


test_df = df_model[
    df_model["date"] >= split_date
].copy()


print(
    "\nTraining period:"
)

print(
    train_df["date"].min(),
    "→",
    train_df["date"].max()
)


print(
    "\nTesting period:"
)

print(
    test_df["date"].min(),
    "→",
    test_df["date"].max()
)


print(
    "\nTrain rows:",
    len(train_df)
)

print(
    "Test rows :",
    len(test_df)
)


# ============================================================
# 14. PREPROCESSING
# ============================================================

categorical_transformer = Pipeline(
    steps=[

        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            )
        ),

        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)


numeric_transformer = Pipeline(
    steps=[

        (
            "imputer",
            SimpleImputer(
                strategy="median"
            )
        )
    ]
)


# ============================================================
# 15. FREIGHT PREPROCESSOR
# ============================================================

freight_preprocessor = ColumnTransformer(
    transformers=[

        (
            "categorical",
            categorical_transformer,
            categorical_features
        ),

        (
            "numeric",
            numeric_transformer,
            [
                col
                for col in freight_features
                if col
                not in categorical_features
            ]
        )
    ]
)


# ============================================================
# 16. TRAIN FREIGHT MODEL
# ============================================================

print(
    "\n"
    + "=" * 70
)

print(
    "              TRAINING FREIGHT MODEL"
)

print(
    "=" * 70
)


freight_model = Pipeline(
    steps=[

        (
            "preprocessor",
            freight_preprocessor
        ),

        (
            "model",
            XGBRegressor(

                n_estimators=500,

                max_depth=6,

                learning_rate=0.05,

                subsample=0.8,

                colsample_bytree=0.8,

                objective="reg:squarederror",

                random_state=42
            )
        )
    ]
)


freight_model.fit(
    train_df[
        freight_features
    ],
    train_df[
        "target_freight_next_day"
    ]
)


print(
    "Freight model trained successfully."
)


# ============================================================
# 17. FREIGHT EVALUATION
# ============================================================

freight_predictions = (
    freight_model.predict(
        test_df[
            freight_features
        ]
    )
)


freight_mae = (
    mean_absolute_error(
        test_df[
            "target_freight_next_day"
        ],
        freight_predictions
    )
)


freight_rmse = np.sqrt(
    mean_squared_error(
        test_df[
            "target_freight_next_day"
        ],
        freight_predictions
    )
)


freight_r2 = r2_score(
    test_df[
        "target_freight_next_day"
    ],
    freight_predictions
)


freight_mape = (
    mean_absolute_percentage_error(
        test_df[
            "target_freight_next_day"
        ],
        freight_predictions
    ) * 100
)


print(
    "\nFREIGHT MODEL RESULTS"
)

print(
    f"MAE  : {freight_mae:.4f}"
)

print(
    f"RMSE : {freight_rmse:.4f}"
)

print(
    f"R2   : {freight_r2:.4f}"
)

print(
    f"MAPE : {freight_mape:.2f}%"
)


# ============================================================
# 18. CONGESTION PREPROCESSOR
# ============================================================

congestion_preprocessor = ColumnTransformer(
    transformers=[

        (
            "categorical",
            categorical_transformer,
            categorical_features
        ),

        (
            "numeric",
            numeric_transformer,
            [
                col
                for col in congestion_features
                if col
                not in categorical_features
            ]
        )
    ]
)


# ============================================================
# 19. TRAIN CONGESTION MODEL
# ============================================================

print(
    "\n"
    + "=" * 70
)

print(
    "             TRAINING CONGESTION MODEL"
)

print(
    "=" * 70
)


congestion_model = Pipeline(
    steps=[

        (
            "preprocessor",
            congestion_preprocessor
        ),

        (
            "model",
            XGBRegressor(

                n_estimators=500,

                max_depth=6,

                learning_rate=0.05,

                subsample=0.8,

                colsample_bytree=0.8,

                objective="reg:squarederror",

                random_state=42
            )
        )
    ]
)


congestion_model.fit(
    train_df[
        congestion_features
    ],
    train_df[
        "target_congestion_next_day"
    ]
)


print(
    "Congestion model trained successfully."
)


# ============================================================
# 20. CONGESTION EVALUATION
# ============================================================

congestion_predictions = (
    congestion_model.predict(
        test_df[
            congestion_features
        ]
    )
)


congestion_mae = (
    mean_absolute_error(
        test_df[
            "target_congestion_next_day"
        ],
        congestion_predictions
    )
)


congestion_rmse = np.sqrt(
    mean_squared_error(
        test_df[
            "target_congestion_next_day"
        ],
        congestion_predictions
    )
)


congestion_r2 = r2_score(
    test_df[
        "target_congestion_next_day"
    ],
    congestion_predictions
)


print(
    "\nCONGESTION MODEL RESULTS"
)

print(
    f"MAE  : {congestion_mae:.4f}"
)

print(
    f"RMSE : {congestion_rmse:.4f}"
)

print(
    f"R2   : {congestion_r2:.4f}"
)


# ============================================================
# 21. SAVE MODELS
# ============================================================

freight_model_path = os.path.join(
    MODEL_DIR,
    "freight_forecasting_model.pkl"
)


congestion_model_path = os.path.join(
    MODEL_DIR,
    "congestion_forecasting_model.pkl"
)


joblib.dump(
    freight_model,
    freight_model_path
)


joblib.dump(
    congestion_model,
    congestion_model_path
)


# ============================================================
# 22. SAVE METADATA
# ============================================================

metadata = {

    "freight_features":
        freight_features,

    "congestion_features":
        congestion_features,

    "freight_mae":
        freight_mae,

    "freight_rmse":
        freight_rmse,

    "freight_r2":
        freight_r2,

    "freight_mape":
        freight_mape,

    "congestion_mae":
        congestion_mae,

    "congestion_rmse":
        congestion_rmse,

    "congestion_r2":
        congestion_r2,

    "train_start":
        str(
            train_df["date"].min()
        ),

    "train_end":
        str(
            train_df["date"].max()
        ),

    "test_start":
        str(
            test_df["date"].min()
        ),

    "test_end":
        str(
            test_df["date"].max()
        )
}


metadata_path = os.path.join(
    MODEL_DIR,
    "model_metadata.pkl"
)


joblib.dump(
    metadata,
    metadata_path
)


# ============================================================
# 23. SAVE EVALUATION RESULTS
# ============================================================

metrics_df = pd.DataFrame({

    "Model": [
        "Freight",
        "Congestion"
    ],

    "MAE": [
        freight_mae,
        congestion_mae
    ],

    "RMSE": [
        freight_rmse,
        congestion_rmse
    ],

    "R2": [
        freight_r2,
        congestion_r2
    ],

    "MAPE": [
        freight_mape,
        np.nan
    ]
})


metrics_path = os.path.join(
    OUTPUT_DIR,
    "model_evaluation_metrics.csv"
)


metrics_df.to_csv(
    metrics_path,
    index=False
)


# ============================================================
# 24. SAVE TEST PREDICTIONS
# ============================================================

test_results = test_df[
    [
        "date",
        "route",
        "vessel_type",
        "target_freight_next_day",
        "target_congestion_next_day"
    ]
].copy()


test_results[
    "predicted_freight"
] = freight_predictions


test_results[
    "predicted_congestion"
] = congestion_predictions


test_results_path = os.path.join(
    OUTPUT_DIR,
    "test_predictions.csv"
)


test_results.to_csv(
    test_results_path,
    index=False
)


# ============================================================
# 25. FINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 70
)

print(
    "                 TRAINING COMPLETE"
)

print(
    "=" * 70
)

print(
    "\nSaved files:"
)

print(
    f"\nFreight model:"
)

print(
    freight_model_path
)

print(
    "\nCongestion model:"
)

print(
    congestion_model_path
)

print(
    "\nMetadata:"
)

print(
    metadata_path
)

print(
    "\nEvaluation metrics:"
)

print(
    metrics_path
)

print(
    "\nTest predictions:"
)

print(
    test_results_path
)

print(
    "\nDone."
)
