# app/anomaly.py
from sklearn.ensemble import IsolationForest
import pandas as pd

def detect_anomaly(user_series: pd.Series):
    model = IsolationForest(random_state=42)
    anomaly_flag = model.fit_predict(user_series.values.reshape(-1,1))
    # 1 = normal, -1 = anomaly
    return anomaly_flag