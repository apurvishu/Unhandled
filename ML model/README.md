# SIH 2026 - AI/ML Freight Forecasting

This folder contains the AI/ML module for the SIH 2026
Intelligent Freight Forecasting and Vessel Chartering project.

## Responsibilities

- Freight-rate forecasting
- Port congestion forecasting
- Multi-horizon forecasting
- Trend analysis
- Model evaluation
- Prediction interface for backend integration

## Forecast Horizons

- Short Term: 1–7 days
- Near Term: 8–14 days
- Medium Term: 15–30 days
- Longer Term: 31–90 days

## Models

### Freight Forecasting

XGBoost Regression

### Congestion Forecasting

XGBoost Regression with:

- LOW
- MEDIUM
- HIGH

## Evaluation Metrics

### Freight

- MAE
- RMSE
- R²
- MAPE
- Within ±5% error

### Congestion

- MAE
- RMSE
- R²
- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix

## Current Status

Prototype implementation using development data.

The ML pipeline will be integrated with the backend and updated with real maritime data as the project progresses.
