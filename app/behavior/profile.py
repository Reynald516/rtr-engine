def build_behavior_profile(
    total_income: int,
    total_expense: int,
    risk_level: str,
    dominant_category: str,
    pattern_memory: dict | None
):
    """
    Bangun profil perilaku user (MVP, rule-based)
    """

    profile = {
        "financial_personality": "UNKNOWN",
        "spending_style": [],
        "risk_trait": [],
        "summary": ""
    }

    # 1. Financial personality
    if risk_level == "LOW":
        profile["financial_personality"] = "STABLE"
    elif risk_level == "MEDIUM":
        profile["financial_personality"] = "BALANCED"
    else:
        profile["financial_personality"] = "RISKY"

    # 2. Spending style
    if dominant_category:
        profile["spending_style"].append(
            f"Fokus pengeluaran pada kategori {dominant_category}"
        )

    if total_expense > total_income:
        profile["spending_style"].append(
            "Cenderung membelanjakan lebih dari pemasukan"
        )

    if pattern_memory:
        if pattern_memory.get("expense_trend") == "INCREASING":
            profile["risk_trait"].append("Pola pengeluaran meningkat dari waktu ke waktu")
        if pattern_memory.get("dominant_category_consistency"):
            profile["spending_style"].append(
                "Pola pengeluaran relatif konsisten"
            )

    # 3. Summary singkat (penting buat UX)
    profile["summary"] = (
        f"Kamu tergolong pengguna dengan profil {profile['financial_personality'].lower()}, "
        f"dengan kecenderungan pengeluaran yang dapat dipetakan."
    )

    return profile