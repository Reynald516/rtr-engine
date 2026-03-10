# app/insights/generator.py

from datetime import date
from .engine_law import RISK_TITLES, WARNING_LEVEL
from .schema import build_insight_response


def generate_insight(analysis_result: dict):
    today = date.today().isoformat()

    risk_level = analysis_result.get("risk_level", "UNKNOWN")
    top_categories = sorted(
        analysis_result.get("category_breakdown", {}).items(),
        key=lambda x: x[1],
        reverse=True
    )
    total_expense = analysis_result.get("total_expense", 0)

    # TITLE
    title = RISK_TITLES.get(risk_level, "Status keuangan kamu hari ini tidak dapat dianalisis")

    # SUMMARY
    if top_categories and total_expense > 0:
        summary = (
            f"Hari ini pengeluaran terbesar kamu ada di kategori "
            f"{top_categories[0][0]} dengan total pengeluaran {total_expense}. "
            f"Secara keseluruhan kondisi keuangan kamu {risk_level.lower()}."
        )
    else:
        summary = (
            f"Hari ini belum ada pengeluaran signifikan yang terdeteksi. "
            f"Secara keseluruhan kondisi keuangan kamu {risk_level.lower()}."
        )

    # PATTERNS
    patterns = []

    # === HABIT WARNING (v1.5) ===
    habit_warning = analysis_result.get("habit_warning")
    
    if habit_warning:
        patterns.append({
            "type": "HABIT_WARNING",
            "level": habit_warning.get("level", "INFO"),
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

    if top_categories and total_expense > 0:
        patterns.append({
            "type": "SPENDING_DOMINANCE",
            "description": f"Sebagian besar pengeluaran kamu terkonsentrasi pada kategori {top_categories[0][0]}."
        })

    if analysis_result.get("income_unstable"):
        patterns.append({
            "type": "INCOME_INSTABILITY",
            "description": "Total pengeluaran kamu lebih besar dibanding pemasukan hari ini."
        })

    if analysis_result.get("anomaly"):
        patterns.append({
            "type": "ANOMALY",
            "description": "Terdapat transaksi yang tidak biasa dibanding pola normal kamu."
        })

    # WARNING
    warning_message_map = {
        "LOW": "Kondisi keuangan kamu stabil hari ini.",
        "MEDIUM": "Ada beberapa pola yang perlu kamu perhatikan.",
        "HIGH": "Pengeluaran kamu perlu segera dikontrol.",
        "DANGER": "Segera evaluasi kondisi keuangan kamu hari ini."
    }
    
    warnings = [{
        "level": WARNING_LEVEL.get(risk_level, "INFO"),
        "message": warning_message_map.get(
            risk_level,
            "Status keuangan tidak dapat ditentukan."
        )
    }]

    # ADVICE
    advice = []

    if top_categories:
        advice.append(f"Pertimbangkan untuk mengatur ulang biaya {top_categories[0][0].lower()}.")

    if analysis_result.get("income_unstable"):
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