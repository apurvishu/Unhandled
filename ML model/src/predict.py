"""
SIH 2026 - ML Prediction Interface

Uses trained model artifacts from:
ML model/models/

Outputs:
- Freight-rate forecast
- Congestion-index forecast
- MEDIUM/HIGH congestion risk
- HIGH congestion probability
- 1-7 day horizon
- 8-14 day horizon
- 15-30 day horizon
- 31-90 day horizon
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ML_DIR = os.path.dirname(
    CURRENT_DIR
)

DATA_PATH = os.path.join(
    ML_DIR,
    "data",
    "SIH_AI_ML_Freight_And_Congestion_Prototype_Dataset.xlsx"
)

MODEL_DIR = os.path.join(
    ML_DIR,
    "models"
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

CONGESTION_CLASSIFIER_PATH = os.path.join(
    MODEL_DIR,
    "congestion_risk_classifier.pkl"
)

THRESHOLD_PATH = os.path.join(
    MODEL_DIR,
    "congestion_threshold.pkl"
)

METADATA_PATH = os.path.join(
    MODEL_DIR,
    "model_metadata.pkl"
)


# ============================================================
# CHECK FILES
# ============================================================

required_files = {
    "Freight model": FREIGHT_MODEL_PATH,
    "Congestion model": CONGESTION_MODEL_PATH,
    "Congestion classifier": CONGESTION_CLASSIFIER_PATH,
    "Congestion threshold": THRESHOLD_PATH,
    "Metadata": METADATA_PATH,
    "Dataset": DATA_PATH
}

for name, path in required_files.items():

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"{name} not found:\n{path}"
        )


# ============================================================
# LOAD MODELS
# ============================================================

freight_model = joblib.load(
    FREIGHT_MODEL_PATH
)

congestion_model = joblib.load(
    CONGESTION_MODEL_PATH
)

congestion_classifier = joblib.load(
    CONGESTION_CLASSIFIER_PATH
)

congestion_threshold = float(
    joblib.load(
        THRESHOLD_PATH
    )
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
# LOAD DATASET
# ============================================================

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
)

df = df.sort_values(
    [
        "route",
        "vessel_type",
        "date"
    ]
).reset_index(drop=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def congestion_level(
    congestion_index
):
    """
    Convert numerical congestion index
    into operational risk level.

    Current prototype dataset:
    <= 60  -> MEDIUM
    > 60   -> HIGH
    """

    if float(congestion_index) <= 60:

        return "MEDIUM"

    return "HIGH"


def freight_trend(
    percentage_change
):
    """
    Determine freight trend.
    """

    value = float(
        percentage_change
    )

    if value > 1:

        return "UP"

    if value < -1:

        return "DOWN"

    return "STABLE"


def get_horizon(
    forecast_day
):
    """
    Map day number to forecasting horizon.
    """

    day = int(
        forecast_day
    )

    if day <= 7:

        return "SHORT_TERM_1_7"

    if day <= 14:

        return "NEAR_TERM_8_14"

    if day <= 30:

        return "MEDIUM_TERM_15_30"

    return "LONGER_TERM_31_90"


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(
    data
):
    """
    Recreate the same feature engineering
    used during training.
    """

    data = data.copy()

    group_keys = [
        "route",
        "vessel_type"
    ]


    # --------------------------------------------------------
    # TIME FEATURES
    # --------------------------------------------------------

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

    data["quarter"] = (
        data["date"].dt.quarter
    )

    data["week_of_year"] = (
        data["date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )


    # --------------------------------------------------------
    # CYCLIC FEATURES
    # --------------------------------------------------------

    data["month_sin"] = np.sin(
        2 * np.pi * data["month"] / 12
    )

    data["month_cos"] = np.cos(
        2 * np.pi * data["month"] / 12
    )

    data["day_of_year_sin"] = np.sin(
        2 * np.pi *
        data["day_of_year"] /
        365
    )

    data["day_of_year_cos"] = np.cos(
        2 * np.pi *
        data["day_of_year"] /
        365
    )


    # --------------------------------------------------------
    # FREIGHT
    # --------------------------------------------------------

    freight_group = (
        data
        .groupby(group_keys)
        ["freight_rate_usd_per_mt"]
    )

    for lag in [
        1,
        2,
        3,
        7,
        14,
        30
    ]:

        data[
            f"freight_lag_{lag}"
        ] = freight_group.shift(lag)


    for window in [
        7,
        14,
        30
    ]:

        data[
            f"freight_rolling_{window}"
        ] = freight_group.transform(
            lambda x, w=window:
            x.shift(1)
            .rolling(w)
            .mean()
        )


    data[
        "freight_change_1d"
    ] = freight_group.pct_change(1)

    data[
        "freight_change_7d"
    ] = freight_group.pct_change(7)

    data[
        "freight_change_30d"
    ] = freight_group.pct_change(30)


    # --------------------------------------------------------
    # CONGESTION
    # --------------------------------------------------------

    congestion_group = (
        data
        .groupby(group_keys)
        ["congestion_index"]
    )

    for lag in [
        1,
        2,
        3,
        7,
        14,
        30
    ]:

        data[
            f"congestion_lag_{lag}"
        ] = congestion_group.shift(lag)


    for window in [
        7,
        14,
        30
    ]:

        data[
            f"congestion_rolling_{window}"
        ] = congestion_group.transform(
            lambda x, w=window:
            x.shift(1)
            .rolling(w)
            .mean()
        )

    return data


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
        Example:
        Indonesia-Paradip

    vessel_type : str
        Example:
        Panamax

    forecast_days : int
        7, 14, 30, or 90

    Returns
    -------
    dict
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    allowed_days = [
        7,
        14,
        30,
        90
    ]

    if forecast_days not in allowed_days:

        raise ValueError(
            "forecast_days must be "
            "7, 14, 30, or 90."
        )


    available_routes = (
        df["route"]
        .dropna()
        .unique()
        .tolist()
    )


    available_vessels = (
        df["vessel_type"]
        .dropna()
        .unique()
        .tolist()
    )


    if route not in available_routes:

        raise ValueError(
            f"Invalid route: {route}. "
            f"Available routes: "
            f"{available_routes}"
        )


    if vessel_type not in available_vessels:

        raise ValueError(
            f"Invalid vessel type: "
            f"{vessel_type}. "
            f"Available types: "
            f"{available_vessels}"
        )


    # --------------------------------------------------------
    # HISTORICAL DATA
    # --------------------------------------------------------

    history = df[
        (df["route"] == route)
        &
        (
            df["vessel_type"]
            == vessel_type
        )
    ].copy()


    history = history.sort_values(
        "date"
    ).reset_index(drop=True)


    if len(history) < 35:

        raise ValueError(
            "Insufficient historical "
            "data for this route/vessel."
        )


    # --------------------------------------------------------
    # CURRENT STATE
    # --------------------------------------------------------

    latest = history.iloc[-1]

    current_date = latest[
        "date"
    ]

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


    results = []

    working_history = (
        history.copy()
    )


    # ========================================================
    # RECURSIVE FORECAST
    # ========================================================

    for forecast_day in range(
        1,
        forecast_days + 1
    ):

        # ----------------------------------------------------
        # Future date
        # ----------------------------------------------------

        future_date = (
            working_history[
                "date"
            ].max()
            +
            pd.Timedelta(days=1)
        )


        latest_row = (
            working_history
            .iloc[-1]
            .copy()
        )


        future_row = (
            latest_row.copy()
        )


        future_row["date"] = (
            future_date
        )


        # ----------------------------------------------------
        # Build feature dataset
        # ----------------------------------------------------

        temporary_history = (
            pd.concat(
                [
                    working_history,
                    pd.DataFrame(
                        [future_row]
                    )
                ],
                ignore_index=True
            )
        )


        temporary_history = (
            create_features(
                temporary_history
            )
        )


        input_row = (
            temporary_history
            .iloc[-1:]
            .copy()
        )


        # ----------------------------------------------------
        # Freight prediction
        # ----------------------------------------------------

        predicted_freight = (
            freight_model.predict(
                input_row[
                    freight_features
                ]
            )[0]
        )


        predicted_freight = float(
            max(
                0,
                predicted_freight
            )
        )


        # ----------------------------------------------------
        # Congestion prediction
        # ----------------------------------------------------

        predicted_congestion = (
            congestion_model.predict(
                input_row[
                    congestion_features
                ]
            )[0]
        )


        predicted_congestion = float(
            np.clip(
                predicted_congestion,
                0,
                100
            )
        )


        # ----------------------------------------------------
        # HIGH probability
        # ----------------------------------------------------

        high_probability = (
            congestion_classifier
            .predict_proba(
                input_row[
                    congestion_features
                ]
            )[0][1]
        )


        high_probability = float(
            high_probability
        )


        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        if (
            high_probability
            >= congestion_threshold
        ):

            risk = "HIGH"

        else:

            risk = "MEDIUM"


        # ----------------------------------------------------
        # Freight change
        # ----------------------------------------------------

        freight_change = (

            (
                predicted_freight
                -
                current_freight
            )

            /

            current_freight

        ) * 100


        # ----------------------------------------------------
        # Horizon
        # ----------------------------------------------------

        horizon = get_horizon(
            forecast_day
        )


        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        results.append({

            "forecast_day":
                forecast_day,

            "date":
                future_date.strftime(
                    "%Y-%m-%d"
                ),

            "freight_rate":
                round(
                    predicted_freight,
                    2
                ),

            "freight_change_percent":
                round(
                    freight_change,
                    2
                ),

            "freight_trend":
                freight_trend(
                    freight_change
                ),

            "congestion_index":
                round(
                    predicted_congestion,
                    2
                ),

            "high_probability":
                round(
                    high_probability * 100,
                    2
                ),

            "congestion_risk":
                risk,

            "forecast_horizon":
                horizon
        })


        # ----------------------------------------------------
        # Feed predictions forward
        # ----------------------------------------------------

        future_row[
            "freight_rate_usd_per_mt"
        ] = predicted_freight

        future_row[
            "congestion_index"
        ] = predicted_congestion


        working_history = (
            pd.concat(
                [
                    working_history,
                    pd.DataFrame(
                        [future_row]
                    )
                ],
                ignore_index=True
            )
        )


    # ========================================================
    # DATAFRAME
    # ========================================================

    forecast_df = pd.DataFrame(
        results
    )


    # ========================================================
    # HORIZON SUMMARY
    # ========================================================

    summary = {}

    horizon_definitions = {

        "short_term_1_7": range(1, 8),

        "near_term_8_14": range(8, 15),

        "medium_term_15_30": range(15, 31),

        "longer_term_31_90": range(31, 91)
    }


    for horizon_name, day_range in (
        horizon_definitions.items()
    ):

        horizon_df = (
            forecast_df[
                forecast_df[
                    "forecast_day"
                ].isin(
                    list(day_range)
                )
            ]
        )


        if horizon_df.empty:

            continue


        average_freight = (
            horizon_df[
                "freight_rate"
            ].mean()
        )


        ending_freight = (
            horizon_df[
                "freight_rate"
            ].iloc[-1]
        )


        average_congestion = (
            horizon_df[
                "congestion_index"
            ].mean()
        )


        peak_congestion = (
            horizon_df[
                "congestion_index"
            ].max()
        )


        average_high_probability = (
            horizon_df[
                "high_probability"
            ].mean()
        )


        freight_change = (

            (
                ending_freight
                -
                current_freight
            )

            /

            current_freight

        ) * 100


        summary[horizon_name] = {

            "average_freight_rate":
                round(
                    float(
                        average_freight
                    ),
                    2
                ),

            "ending_freight_rate":
                round(
                    float(
                        ending_freight
                    ),
                    2
                ),

            "freight_change_percent":
                round(
                    float(
                        freight_change
                    ),
                    2
                ),

            "freight_trend":
                freight_trend(
                    freight_change
                ),

            "average_congestion":
                round(
                    float(
                        average_congestion
                    ),
                    2
                ),

            "peak_congestion":
                round(
                    float(
                        peak_congestion
                    ),
                    2
                ),

            "average_high_probability":
                round(
                    float(
                        average_high_probability
                    ),
                    2
                ),

            "congestion_risk":
                congestion_level(
                    average_congestion
                )
        }


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "route":
            route,

        "vessel_type":
            vessel_type,

        "current_conditions": {

            "date":
                current_date.strftime(
                    "%Y-%m-%d"
                ),

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

            "congestion_risk":
                congestion_level(
                    current_congestion
                )
        },

        "forecast_days":
            forecast_days,

        "horizons":
            summary,

        "daily_forecast":
            results
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    result = predict(
        route="Indonesia-Paradip",
        vessel_type="Panamax",
        forecast_days=90
    )


    print()
    print("=" * 70)
    print("           SIH 2026 ML PREDICTION")
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
        "\nCurrent Conditions:"
    )

    print(
        result[
            "current_conditions"
        ]
    )

    print(
        "\nFour-Horizon Forecast:"
    )

    for (
        horizon,
        values
    ) in result[
        "horizons"
    ].items():

        print(
            f"\n{horizon}"
        )

        print(
            values
        )

    print(
        "\nDaily forecast rows:",
        len(
            result[
                "daily_forecast"
            ]
        )
    )
