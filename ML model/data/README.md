# ML Dataset

This folder contains the datasets used by the AI/ML module of the SIH 2026 Intelligent Freight Forecasting and Vessel Chartering project.

## Purpose

The data is used to train and evaluate two machine learning models:

1. **Freight-Rate Forecasting**
2. **Port Congestion Forecasting**

The models generate forecasts for four time horizons:

- Short Term: 1–7 days
- Near Term: 8–14 days
- Medium Term: 15–30 days
- Longer Term: 31–90 days

## Dataset Features

The prototype dataset includes:

### Freight and Market
- Freight rate
- Fuel price index
- Commodity price index
- Route
- Vessel type

### Vessel
- DWT
- LOA
- Beam
- Draft
- Distance

### AIS / Vessel Activity
- Vessel density
- Approaching vessels
- Average vessel speed

### Port Performance
- Port calls
- Median time in port
- Average DWT
- Berth utilization
- Average waiting time

### Weather
- Weather severity
- Wind speed
- Wave height

### Congestion
- Congestion index
- Congestion level

## Forecast Targets

### Freight Model

Predicts the future freight rate in USD per metric tonne:

`freight_rate_usd_per_mt`

### Congestion Model

Predicts the future congestion index:

`congestion_index`

The congestion index is interpreted as:

- **0–30:** LOW
- **31–60:** MEDIUM
- **61–100:** HIGH

## Current Dataset Status

The current Excel dataset is a **synthetic prototype dataset** created for development, testing, feature engineering, and model pipeline validation.

It should not be interpreted as actual historical market observations.

The final system will incorporate real-world maritime data from appropriate AIS, port, weather, fuel, commodity, and freight-rate sources and the models will then be retrained and reevaluated.

## Expected Dataset File

The development dataset used by the current ML code is:

`SIH_AI_ML_Freight_And_Congestion_Prototype_Dataset.xlsx`

The Python training pipeline expects the file to be located in this directory:

`ML model/data/`
