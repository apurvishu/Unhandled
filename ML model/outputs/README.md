# ML Outputs

This folder contains the generated outputs from the SIH 2026 AI/ML forecasting pipeline.

## Main Result File

`SIH2026_ML_Final_Results.xlsx`

The workbook contains:

### 90_Day_Forecast
Daily predictions for up to 90 days.

Includes:
- Forecast date
- Predicted freight rate
- Freight-rate change
- Predicted congestion index
- HIGH-congestion probability
- Congestion risk
- Forecast horizon

### Four_Horizons

Forecast summaries for:

- Short Term: 1–7 days
- Near Term: 8–14 days
- Medium Term: 15–30 days
- Longer Term: 31–90 days

### Model_Metrics

Evaluation metrics for:

#### Freight model
- MAE
- RMSE
- R²
- MAPE
- Within ±5%
- Within ±10%

#### Congestion model
- MAE
- RMSE
- R²

#### Congestion classifier
- Accuracy
- Precision
- Recall
- F1 Score

## Dataset Note

These results were generated using the current prototype development dataset. They should not be interpreted as production-level real-world forecasting performance.
