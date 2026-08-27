"""
SIH 2026 - ML Prediction Interface
-----------------------------------

This file provides a simple interface for:
- Freight-rate prediction
- Congestion prediction
- 7/14/30/90-day forecasting

It is designed to be called later by the backend API.

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
└── src/
    ├── train_models.py
    ├── forecast.py
    ├── metrics.py
    └── predict.py
"""

import os
import sys
import joblib
import pandas as pd


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


# ============================================================
# IMPORT FORECAST FUNCTION
# ============================================================

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

from forecast import forecast_route


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

metadata_path = os.path.join(
    MODEL_DIR,
    "model_metadata.pkl"
)


if not os.path.exists(
    freight_model_path
):
    raise FileNotFoundError(
        "Freight model not found.\n"
        f"Expected:\n{freight_model_path}\n"
        "Run train_models.py first."
    )


if not os.path.exists(
    congestion_model_path
):
    raise FileNotFoundError(
        "Congestion model not found.\n"
        f"Expected:\n{congestion_model_path}\n"
        "Run train_models.py first."
    )


if not os.path.exists(
    metadata_path
):
    raise FileNotFoundError(
        "Model metadata not found.\n"
        f"Expected:\n{metadata_path}\n"
        "Run train_models.py first."
    )


freight_model = joblib.load(
    freight_model_path
)

congestion_model = joblib.load(
    congestion_model_path
)

metadata = joblib.load(
    metadata_path
)


# ============================================================
# LOAD DATA
# ============================================================

if not os.path.exists(
    DATA_PATH
):
    raise FileNotFoundError(
        "Dataset not found.\n"
        f"Expected:\n{DATA_PATH}"
    )


df = pd.read_excel(
    DATA_PATH,
    sheet_name="Final_ML_Dataset"
)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)


# ============================================================
# CONGESTION CLASSIFICATION
# ============================================================

def congestion_level(
    value
):
    """
    Convert congestion index
    into a business-friendly level.
    """

    value = float(value)

    if value <= 30:
        return "LOW"

    elif value <= 60:
        return "MEDIUM"

    return "HIGH"


# ============================================================
# FREIGHT TREND
# ============================================================

def freight_trend(
    percentage_change
):
    """
    Convert freight percentage change
    into a trend label.
    """

    percentage_change = float(
        percentage_change
    )

    if percentage_change > 1:
        return "UP"

    elif percentage_change < -1:
        return "DOWN"

    return "STABLE"


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict(
    route,
    vessel_type,
    forecast_days=90
):
    """
    Generate freight and congestion forecasts.

    Parameters
    ----------
    route : str
        Example: "Indonesia-Paradip"

    vessel_type : str
        Example: "Panamax"

    forecast_days : int
        Allowed values: 7, 14, 30, 90

    Returns
    -------
    dict
        Complete forecast response.
    """

    # --------------------------------------------------------
    # Validate forecast horizon
    # --------------------------------------------------------

    if forecast_days not in [
        7,
        14,
        30,
        90
    ]:
        raise ValueError(
            "forecast_days must be "
            "7, 14, 30 or 90."
        )


    # --------------------------------------------------------
    # Validate route
    # --------------------------------------------------------

    if route not in df[
        "route"
    ].dropna().unique():

        raise ValueError(
            f"Unknown route: {route}"
        )


    # --------------------------------------------------------
    # Validate vessel
    # --------------------------------------------------------

    if vessel_type not in df[
        "vessel_type"
    ].dropna().unique():

        raise ValueError(
            f"Unknown vessel type: "
            f"{vessel_type}"
        )


    # --------------------------------------------------------
    # Select history
    # --------------------------------------------------------

    history = df[
        (
            df["route"]
            == route
        )
        &
        (
            df["vessel_type"]
            == vessel_type
        )
    ].copy()


    history = history.sort_values(
        "date"
    ).reset_index(
        drop=True
    )


    # --------------------------------------------------------
    # Minimum history
    # --------------------------------------------------------

    if len(history) < 35:

        raise ValueError(
            "At least 35 historical "
            "records are required."
        )


    # --------------------------------------------------------
    # Current state
    # --------------------------------------------------------

    latest = history.iloc[-1]

    current_date = (
        latest["date"]
    )

    current_freight = float(
        latest[
            "freight_rate_usd_per_mt"
        ]
    )

    current_congestion = float(
        latest[
            "congestion_index"
        ]
    )


    # --------------------------------------------------------
    # Forecast
    # --------------------------------------------------------

    forecast_df = forecast_route(
        history=history,
        days=forecast_days
    )


    # --------------------------------------------------------
    # Add horizon
    # --------------------------------------------------------

    def horizon(day):

        if day <= 7:
            return "SHORT_TERM"

        elif day <= 14:
            return "NEAR_TERM"

        elif day <= 30:
            return "MEDIUM_TERM"

        else:
            return "LONGER_TERM"


    forecast_df[
        "horizon"
    ] = forecast_df[
        "forecast_day"
    ].apply(
        horizon
    )


    # --------------------------------------------------------
    # Add freight change from current
    # --------------------------------------------------------

    forecast_df[
        "change_from_current_percent"
    ] = (

        (
            forecast_df[
                "predicted_freight_rate"
            ]
            -
            current_freight
        )

        /

        current_freight

    ) * 100


    # --------------------------------------------------------
    # Create horizon summary
    # --------------------------------------------------------

    summary = (
        forecast_df
        .groupby(
            "horizon"
        )
        .agg(

            average_freight_rate=(
                "predicted_freight_rate",
                "mean"
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


    # --------------------------------------------------------
    # Horizon freight changes
    # --------------------------------------------------------

    summary[
        "freight_change_percent"
    ] = (

        (
            summary[
                "ending_freight_rate"
            ]
            -
            current_freight
        )

        /

        current_freight

    ) * 100


    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Congestion risk
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Convert DataFrames into JSON-like objects
    # --------------------------------------------------------

    daily_forecast = []

    for _, row in forecast_df.iterrows():

        daily_forecast.append({

            "day":
                int(
                    row["forecast_day"]
                ),

            "date":
                str(
                    row["date"].date()
                ),

            "freight_rate":
                round(
                    float(
                        row[
                            "predicted_freight_rate"
                        ]
                    ),
                    2
                ),

            "freight_change_percent":
                round(
                    float(
                        row[
                            "change_from_current_percent"
                        ]
                    ),
                    2
                ),

            "congestion_index":
                round(
                    float(
                        row[
                            "predicted_congestion_index"
                        ]
                    ),
                    2
                ),

            "congestion_level":
                row[
                    "congestion_level"
                ],

            "horizon":
                row["horizon"]
        })


    # --------------------------------------------------------
    # Create summary dictionary
    # --------------------------------------------------------

    horizon_summary = {}

    for _, row in summary.iterrows():

        horizon_summary[
            row["horizon"]
        ] = {

            "average_freight_rate":
                round(
                    float(
                        row[
                            "average_freight_rate"
                        ]
                    ),
                    2
                ),

            "ending_freight_rate":
                round(
                    float(
                        row[
                            "ending_freight_rate"
                        ]
                    ),
                    2
                ),

            "freight_change_percent":
                round(
                    float(
                        row[
                            "freight_change_percent"
                        ]
                    ),
                    2
                ),

            "freight_trend":
                row[
                    "freight_trend"
                ],

            "average_congestion":
                round(
                    float(
                        row[
                            "average_congestion"
                        ]
                    ),
                    2
                ),

            "peak_congestion":
                round(
                    float(
                        row[
                            "peak_congestion"
                        ]
                    ),
                    2
                ),

            "congestion_risk":
                row[
                    "congestion_risk"
                ]
        }


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    response = {

        "route":
            route,

        "vessel_type":
            vessel_type,

        "forecast_start_date":
            str(
                current_date.date()
            ),

        "forecast_days":
            forecast_days,

        "current_conditions": {

            "freight_rate":
                round(
                    current_freight,
                    2
                ),

            "congestion_index":
                round(
                    current_congestion,
                    2
                ),

            "congestion_level":
                congestion_level(
                    current_congestion
                )
        },

        "horizons":
            horizon_summary,

        "daily_forecast":
            daily_forecast
    }


    return response


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    result = predict(
        route="Indonesia-Paradip",
        vessel_type="Panamax",
        forecast_days=90
    )


    print("\n")
    print("=" * 70)
    print("             AI/ML FORECAST RESULT")
    print("=" * 70)

    print(
        "\nRoute:",
        result["route"]
    )

    print(
        "Vessel:",
        result["vessel_type"]
    )

    print(
        "Current Freight:",
        result[
            "current_conditions"
        ]["freight_rate"]
    )

    print(
        "Current Congestion:",
        result[
            "current_conditions"
        ]["congestion_index"]
    )

    print("\nFOUR HORIZONS")

    for horizon_name, values in (
        result["horizons"].items()
    ):

        print(
            f"\n{horizon_name}"
        )

        print(
            "Average Freight:",
            values[
                "average_freight_rate"
            ]
        )

        print(
            "Ending Freight:",
            values[
                "ending_freight_rate"
            ]
        )

        print(
            "Freight Change:",
            values[
                "freight_change_percent"
            ],
            "%"
        )

        print(
            "Freight Trend:",
            values[
                "freight_trend"
            ]
        )

        print(
            "Average Congestion:",
            values[
                "average_congestion"
            ]
        )

        print(
            "Peak Congestion:",
            values[
                "peak_congestion"
            ]
        )

        print(
            "Congestion Risk:",
            values[
                "congestion_risk"
            ]
        )
