# app/logic.py

def rtr_logic(cluster, anomaly_flag, night_ratio):
    risk = "LOW"
    if cluster == 1 and -1 in anomaly_flag and night_ratio > 0.4:
        risk = "HIGH"
    elif -1 in anomaly_flag:
        risk = "MEDIUM"
    return risk