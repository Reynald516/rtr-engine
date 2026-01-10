# app/trend.py
import pandas as pd

def detect_trend(daily_spend_series: pd.Series):
    rolling_mean = daily_spend_series.rolling(7).mean()
    trend = rolling_mean.diff().fillna(0)
    return trend