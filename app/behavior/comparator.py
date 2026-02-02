# app/behavior/comparator.py

def compare_behavior(today: dict, yesterday: dict):
    expense_change = today["total_expense"] - yesterday["total_expense"]
    income_change = today["total_income"] - yesterday["total_income"]

    if today["risk_level"] == yesterday["risk_level"]:
        risk_change = "STABLE"
    else:
        risk_change = f"{yesterday['risk_level']} → {today['risk_level']}"

    if expense_change > 0:
        behavior_label = "SPENDING_UP"
    elif expense_change < 0:
        behavior_label = "SPENDING_DOWN"
    else:
        behavior_label = "NO_CHANGE"

    summary = (
        f"Perubahan pengeluaran {expense_change}, "
        f"perubahan pemasukan {income_change}, "
        f"risiko {risk_change}"
    )

    return {
        "expense_change": expense_change,
        "income_change": income_change,
        "risk_change": risk_change,
        "behavior_label": behavior_label,
        "summary": summary
    }