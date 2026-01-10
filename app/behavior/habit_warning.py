# app/behavior/habit_warning.py

def detect_habit_warning(
    pattern_memory: dict | None,
    dominant_category: str | None
):
    """
    Deteksi kebiasaan sederhana (MVP-level)
    Fokus: konsistensi & tren
    """

    if not pattern_memory:
        return None

    warning = {
        "level": "SOFT",
        "message": ""
    }

    # 1. Konsistensi kategori
    if pattern_memory.get("dominant_category_consistency") and dominant_category:
        warning["message"] = (
            f"Pengeluaran kamu cukup konsisten di kategori {dominant_category}. "
            f"Ini bisa jadi kebiasaan yang perlu kamu perhatikan."
        )

    # 2. Tren meningkat
    if pattern_memory.get("expense_trend") == "INCREASING":
        warning["level"] = "MEDIUM"
        warning["message"] = (
            "Pengeluaran kamu menunjukkan tren meningkat dalam beberapa hari terakhir. "
            "Coba cek apakah ini kebutuhan atau kebiasaan."
        )

    if warning["message"] == "":
        return None

    return warning