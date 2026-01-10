def evaluate_evolution(today: dict, previous: dict):
    """
    Bandingkan analisis hari ini dengan analisis sebelumnya
    """

    evolution = {
        "trend": "STABLE",
        "changes": [],
        "confidence": "LOW"
    }

    # 1. Bandingkan total expense
    expense_diff = today["total_expense"] - previous["total_expense"]
    expense_pct = expense_diff / max(previous["total_expense"], 1)

    if expense_pct > 0.2:
        evolution["trend"] = "WORSENING"
        evolution["changes"].append(
            f"Pengeluaran naik {int(expense_pct * 100)}% dibanding analisis sebelumnya"
        )
    elif expense_pct < -0.2:
        evolution["trend"] = "IMPROVING"
        evolution["changes"].append(
            f"Pengeluaran turun {int(abs(expense_pct) * 100)}% dibanding analisis sebelumnya"
        )

    # 2. Risk level berubah?
    if today["risk_level"] != previous["risk_level"]:
        evolution["changes"].append(
            f"Risk level berubah dari {previous['risk_level']} ke {today['risk_level']}"
        )

    # 3. Dominant category konsisten?
    if today["dominant_category"] == previous["dominant_category"]:
        evolution["changes"].append(
            f"Kategori {today['dominant_category']} konsisten dominan"
        )

    # Confidence
    if evolution["changes"]:
        evolution["confidence"] = "MEDIUM"

    return evolution