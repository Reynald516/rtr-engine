def analyze_pattern_memory(recent_analyses: list):
    """
    Analisis pola sederhana dari beberapa hari terakhir
    """
    if any(a.get("total_expense") is None for a in recent_analyses):
        return {
            "days_observed": len(recent_analyses),
            "notes": ["Data historis belum lengkap untuk analisis pola."]
        }

    if len(recent_analyses) < 2:
        return None

    total_expenses = [
        a["total_expense"] or 0
        for a in recent_analyses
    ]
    risk_levels = [a["risk_level"] for a in recent_analyses]
    dominant_categories = [a["dominant_category"] for a in recent_analyses]

    avg_expense = sum(total_expenses) / len(total_expenses)

    pattern = {
        "days_observed": len(recent_analyses),
        "avg_daily_expense": int(avg_expense),
        "expense_trend": "STABLE",
        "risk_consistency": len(set(risk_levels)) == 1,
        "dominant_category_consistency": len(set(dominant_categories)) == 1,
        "notes": []
    }

    # Trend sederhana
    if total_expenses[0] > total_expenses[-1] * 1.2:
        pattern["expense_trend"] = "INCREASING"
        pattern["notes"].append("Pengeluaran cenderung meningkat dalam beberapa hari terakhir")
    elif total_expenses[0] < total_expenses[-1] * 0.8:
        pattern["expense_trend"] = "DECREASING"
        pattern["notes"].append("Pengeluaran cenderung menurun dalam beberapa hari terakhir")

    if pattern["dominant_category_consistency"]:
        pattern["notes"].append(
            f"Kategori {dominant_categories[0]} terus mendominasi pengeluaran"
        )

    return pattern