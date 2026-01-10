# app/insights/generator.py

from datetime import date
from .engine_law import RISK_TITLES, WARNING_LEVEL
from .schema import build_insight_response


def generate_insight(analysis_result: dict):
    today = date.today().isoformat()

    risk_level = analysis_result["risk_level"]
    dominant_category = analysis_result.get("dominant_category")
    total_expense = analysis_result.get("total_expense", 0)
    total_income = analysis_result.get("total_income", 0)
    anomaly = analysis_result.get("anomaly", False)

    # TITLE
    title = RISK_TITLES[risk_level]

    # SUMMARY
    summary = (
        f"Hari ini pengeluaran terbesar kamu ada di kategori "
        f"{dominant_category} dengan total pengeluaran {total_expense}. "
        f"Secara keseluruhan kondisi keuangan kamu {risk_level.lower()}."
    )

    # PATTERNS
    patterns = []

    # === HABIT WARNING (v1.5) ===
    habit_warning = analysis_result.get("habit_warning")
    
    if habit_warning:
        patterns.append({
            "type": "HABIT_WARNING",
            "level": habit_warning.get("level"),
            "description": habit_warning.get("message")
        })

    # === BEHAVIOR PROFILE (v1.4) ===
    behavior_profile = analysis_result.get("behavior_profile")
    
    if behavior_profile:
        patterns.append({
            "type": "USER_PROFILE",
            "description": behavior_profile.get("summary")
        })
        
        for style in behavior_profile.get("spending_style", []):
            patterns.append({
                "type": "SPENDING_STYLE",
                "description": style
            })
            
        for risk in behavior_profile.get("risk_trait", []):
            patterns.append({
                "type": "BEHAVIOR_RISK",
                "description": risk
            })

    pattern_memory = analysis_result.get("pattern_memory")
    
    if pattern_memory:
        if "expense_trend" in pattern_memory:
            patterns.append({
                "type": "EXPENSE_TREND",
                "description": f"Pengeluaran kamu cenderung {pattern_memory['expense_trend'].lower()} dalam beberapa hari terakhir."
            })
            
        for note in pattern_memory.get("notes", []):
            patterns.append({
                "type": "PATTERN_MEMORY",
                "description": note
            })

    if dominant_category:
        patterns.append({
            "type": "SPENDING_DOMINANCE",
            "description": f"Sebagian besar pengeluaran kamu terkonsentrasi pada kategori {dominant_category}."
        })

    if total_expense > total_income:
        patterns.append({
            "type": "INCOME_INSTABILITY",
            "description": "Total pengeluaran kamu lebih besar dibanding pemasukan hari ini."
        })

    if anomaly:
        patterns.append({
            "type": "ANOMALY",
            "description": "Terdapat transaksi yang tidak biasa dibanding pola normal kamu."
        })

    # WARNING
    warnings = [{
        "level": WARNING_LEVEL[risk_level],
        "message": "Pola keuangan kamu masih dalam batas yang dapat dianalisis."
    }]

    # ADVICE
    advice = []

    if dominant_category:
        advice.append(f"Pertimbangkan untuk mengatur ulang biaya {dominant_category.lower()}.")

    if total_expense > total_income:
        advice.append("Coba evaluasi pengeluaran agar tidak melebihi pemasukan.")

    return build_insight_response(
        analysis_date=today,
        risk_level=risk_level,
        title=title,
        summary=summary,
        patterns=patterns,
        warnings=warnings,
        advice=advice[:3]
    )