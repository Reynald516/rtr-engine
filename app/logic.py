# app/logic.py

def rtr_logic(cluster, anomaly_flag, night_ratio):
    if cluster == 1 and -1 in anomaly_flag and night_ratio > 0.6:
        return "DANGER"
    
    if cluster == 1 and -1 in anomaly_flag and night_ratio > 0.4:
        return "HIGH"
    
    if -1 in anomaly_flag:
        return "MEDIUM"
    
    return "LOW"