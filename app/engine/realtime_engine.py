# app/engine/realtime_engine.py


def run_realtime_analysis(context: dict) -> dict:
    """
    Lightweight real-time analysis (no heavy ML)
    """
    
    total_income = context.get("total_income", 0)
    total_expense = context.get("total_expense", 0)
    
    net_cashflow = total_income - total_expense
    
    anomaly = None
    if total_expense > total_income * 1.5:
        anomaly = "Overspending detected"
    
    return {
        "net_cashflow": net_cashflow,
        "anomaly": anomaly
    }
