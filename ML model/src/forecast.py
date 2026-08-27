"""
SIH 2026 - Freight & Congestion Forecasting
--------------------------------------------

Generates:
- 1 to 90 day freight-rate forecasts
- 1 to 90 day congestion forecasts
- Four forecasting horizons:
    1-7 days
    8-14 days
    15-30 days
    31-90 days
"""

import os
import joblib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
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
# LOAD MODELS
# ============================================================

freight_model_path = os.path.join(
    MODEL_DIR,
    "freight_forecasting_model.pkl"
)

congestion_model_path = os.path.join(
    MODEL_DIR,
    "congestion_forecasting_model.pkl"
)


if not os.path.exists(freight_model_path):
    raise FileNotFoundError(
        f"Freight model not found:\n{freight_model_path}"
    )

if not os.path.exists(congestion_model_path):
    raise FileNotFoundError(
        f"Congestion model not found:\n{congestion_model_path}"
    )


freight_model = joblib.load(
    freight_model_path
)

congestion_model = joblib.load(
    congestion_model_path
)


# ============================================================
# LOAD METADATA
# ============================================================

metadata_path = os.path.join(
    MODEL_DIR,
    "model_metadata.pkl"
)


if not os.path.exists(metadata_path):
    raise FileNotFoundError(
        f"Metadata not found:\n{metadata_path}"
    )


metadata = joblib.load(
    metadata_path
)


freight_features = metadata[
    "freight_features"
]

congestion_features = metadata[
    "congestion_features"
]


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_excel(
    DATA_PATH,
    sheet_name="Final_ML_Dataset"
)

df["date"] = pd.to_datetime(
    df["date"]
)

df = df.sort_values(
    [
        "route",
        "vessel_type",
        "date"
    ]
).reset_index(drop=True)


# ============================================================
# CONGESTION LEVEL
# ============================================================

def congestion_level(value):

    value = float(value)

    if value <= 30:
        return "LOW"

    if value <= 60:
        return "MEDIUM"

    return "HIGH"


# ============================================================
# TIME FEATURES
# ============================================================

def add_time_features(data):

    data = data.copy()

    data["year"] = (
        data["date"].dt.year
    )

    data["month"] = (
        data["date"].dt.month
    )

    data["day"] = (
        data["date"].dt.day
    )

    data["day_of_week"] = (
        data["date"].dt.dayofweek
    )

    data["day_of_year"] = (
        data["date"].dt.dayofyear
    )

    data["week_of_year"] = (
        data["date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    data["quarter"] = (
        data["date"].dt.quarter
    )

    data["month_sin"] = np.sin(
        2 * np.pi
        * data["month"]
        / 12
    )

    data["month_cos"] = np.cos(
        2 * np.pi
        * data["month"]
        / 12
    )

    data["day_of_year_sin"] = np.sin(
        2 * np.pi
        * data["day_of_year"]
        / 365
    )

    data["day_of_year_cos"] = np.cos(
        2 * np.pi
        * data["day_of_year"]
        / 365
    )

    return data


# ============================================================
# LAG FEATURES
# ============================================================

def add_lag_features(
    data,
    column,
    prefix
):

    data = data.copy()

    grouped = data.groupby(
        [
            "route",
            "vessel_type"
        ]
    )[column]

    for lag in [
        1,
        2,
        3,
        7,
        14,
        30
    ]:

        data[
            f"{prefix}_lag_{lag}"
        ] = grouped.shift(lag)

    data[
        f"{prefix}_rolling_7"
    ] = grouped.transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .mean()
    )

    data[
        f"{prefix}_rolling_14"
    ] = grouped.transform(
        lambda x:
        x.shift(1)
        .rolling(14)
        .mean()
    )

    data[
        f"{prefix}_rolling_30"
    ] = grouped.transform(
        lambda x:
        x.shift(1)
        .rolling(30)
        .mean()
    )

    data[
        f"{prefix}_change_1d"
    ] = grouped.pct_change(1)

    data[
        f"{prefix}_change_7d"
    ] = grouped.pct_change(7)

    data[
        f"{prefix}_change_30d"
    ] = grouped.pct_change(30)

    return data


# ============================================================
# PREPARE HISTORICAL DATA
# ============================================================

df = add_time_features(df)

df = add_lag_features(
    df,
    "freight_rate_usd_per_mt",
    "freight"
)

df = add_lag_features(
    df,
    "congestion_index",
    "congestion"
)


# ============================================================
# FORECAST ONE ROUTE + VESSEL TYPE
# ============================================================

def forecast_route(
    history,
    days=90
):

    history = history.copy()

    history = history.sort_values(
        "date"
    ).reset_index(drop=True)

    results = []

    route = history.iloc[-1]["route"]

    vessel_type = history.iloc[-1][
        "vessel_type"
    ]

    for forecast_day in range(
        1,
        days + 1
    ):

        # ----------------------------------------------------
        # Future date
        # ----------------------------------------------------

        future_date = (
            history["date"].max()
            +
            pd.Timedelta(days=1)
        )


        latest = (
            history.iloc[-1]
        )


        # ----------------------------------------------------
        # Create future row
        # ----------------------------------------------------

        future_row = {}

        for column in history.columns:

            future_row[column] = (
                latest[column]
            )

        future_row["date"] = (
            future_date
        )

        future_row = pd.DataFrame(
            [future_row]
        )


        # ----------------------------------------------------
        # Update time features
        # ----------------------------------------------------

        future_row = add_time_features(
            future_row
        )


        # ----------------------------------------------------
        # Append temporarily
        # ----------------------------------------------------

        temp = pd.concat(
            [
                history,
                future_row
            ],
            ignore_index=True
        )


        # ----------------------------------------------------
        # Recalculate lag features
        # ----------------------------------------------------

        temp = add_lag_features(
            temp,
            "freight_rate_usd_per_mt",
            "freight"
        )

        temp = add_lag_features(
            temp,
            "congestion_index",
            "congestion"
        )


        input_row = (
            temp.iloc[-1:]
            .copy()
        )


        # ----------------------------------------------------
        # Predict congestion
        # ----------------------------------------------------

        congestion_prediction = (
            congestion_model.predict(
                input_row[
                    congestion_features
                ]
            )[0]
        )


        congestion_prediction = max(
            0,
            min(
                100,
                float(
                    congestion_prediction
                )
            )
        )


        # ----------------------------------------------------
        # Predict freight
        # ----------------------------------------------------

        freight_prediction = (
            freight_model.predict(
                input_row[
                    freight_features
                ]
            )[0]
        )


        freight_prediction = max(
            0,
            float(
                freight_prediction
            )
        )


        # ----------------------------------------------------
        # Current freight
        # ----------------------------------------------------

        current_freight = float(
            latest[
                "freight_rate_usd_per_mt"
            ]
        )


        freight_change = (
            (
                freight_prediction
                -
                current_freight
            )
            /
            current_freight
        ) * 100


        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        results.append({

            "forecast_day":
                forecast_day,

            "date":
                future_date,

            "route":
                route,

            "vessel_type":
                vessel_type,

            "predicted_freight_rate":
                round(
                    freight_prediction,
                    4
                ),

            "freight_change_percent":
                round(
                    freight_change,
                    4
                ),

            "predicted_congestion_index":
                round(
                    congestion_prediction,
                    4
                ),

            "congestion_level":
                congestion_level(
                    congestion_prediction
                )
        })


        # ----------------------------------------------------
        # IMPORTANT:
        # Feed predictions back into the history so the next
        # day can use the previous prediction as a lag.
        # ----------------------------------------------------

        future_row[
            "freight_rate_usd_per_mt"
        ] = freight_prediction

        future_row[
            "congestion_index"
        ] = congestion_prediction


        history = pd.concat(
            [
                history,
                future_row
            ],
            ignore_index=True
        )


    return pd.DataFrame(
        results
    )


# ============================================================
# HORIZON FUNCTION
# ============================================================

def get_horizon(day):

    if 1 <= day <= 7:

        return "Short Term (1-7 days)"

    elif 8 <= day <= 14:

        return "Near Term (8-14 days)"

    elif 15 <= day <= 30:

        return "Medium Term (15-30 days)"

    else:

        return "Longer Term (31-90 days)"


# ============================================================
# FORECAST ALL ROUTES + VESSELS
# ============================================================

all_forecasts = []


for (
    route,
    vessel_type
), group in df.groupby(
    [
        "route",
        "vessel_type"
    ]
):

    print(
        f"Forecasting: "
        f"{route} | {vessel_type}"
    )

    if len(group) < 35:

        print(
            "  Skipped: insufficient history."
        )

        continue


    result = forecast_route(
        group,
        days=90
    )


    result[
        "forecast_horizon"
    ] = (
        result[
            "forecast_day"
        ].apply(
            get_horizon
        )
    )


    all_forecasts.append(
        result
    )


# ============================================================
# COMBINE RESULTS
# ============================================================

if not all_forecasts:

    raise RuntimeError(
        "No route/vessel combination "
        "had enough historical data."
    )


forecast_df = pd.concat(
    all_forecasts,
    ignore_index=True
)


# ============================================================
# CREATE HORIZON SUMMARY
# ============================================================

summary = (
    forecast_df
    .groupby(
        [
            "route",
            "vessel_type",
            "forecast_horizon"
        ]
    )
    .agg(

        average_freight_rate=(
            "predicted_freight_rate",
            "mean"
        ),

        starting_freight_rate=(
            "predicted_freight_rate",
            "first"
        ),

        ending_freight_rate=(
            "predicted_freight_rate",
            "last"
        ),

        average_congestion=(
            "predicted_congestion_index",
            "mean"
        ),

        peak_congestion=(
            "predicted_congestion_index",
            "max"
        )
    )
    .reset_index()
)


# ============================================================
# TREND
# ============================================================

summary[
    "freight_change_percent"
] = (

    (
        summary[
            "ending_freight_rate"
        ]
        -
        summary[
            "starting_freight_rate"
        ]
    )

    /

    summary[
        "starting_freight_rate"
    ]

) * 100


def freight_trend(value):

    if value > 1:
        return "UP"

    elif value < -1:
        return "DOWN"

    return "STABLE"


summary[
    "freight_trend"
] = (
    summary[
        "freight_change_percent"
    ]
    .apply(
        freight_trend
    )
)


summary[
    "congestion_risk"
] = (
    summary[
        "average_congestion"
    ]
    .apply(
        congestion_level
    )
)


# ============================================================
# SAVE DAILY FORECAST
# ============================================================

daily_path = os.path.join(
    OUTPUT_DIR,
    "90_day_daily_forecasts.csv"
)


forecast_df.to_csv(
    daily_path,
    index=False
)


# ============================================================
# SAVE FOUR-HORIZON SUMMARY
# ============================================================

summary_path = os.path.join(
    OUTPUT_DIR,
    "four_horizon_summary.csv"
)


summary.to_csv(
    summary_path,
    index=False
)


# ============================================================
# PRINT FINAL OUTPUT
# ============================================================

print("\n")
print("=" * 70)
print("              90-DAY FORECAST COMPLETE")
print("=" * 70)

print(
    f"Daily forecast saved to:\n"
    f"{daily_path}"
)

print(
    f"\nHorizon summary saved to:\n"
    f"{summary_path}"
)

print(
    "\nFour forecasting horizons:"
)

print(
    "1. Short Term  : 1-7 days"
)

print(
    "2. Near Term   : 8-14 days"
)

print(
    "3. Medium Term : 15-30 days"
)

print(
    "4. Longer Term : 31-90 days"
)

print("\nForecast generation finished.")
