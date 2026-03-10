# tests/test_insight.py

from app.insights.generator import generate_insight


# ==================================
# 1️⃣ LOW RISK
# ==================================
def test_generate_insight_low():
    analysis_result = {
        "risk_level": "LOW",
        "dominant_category": "Food",
        "total_expense": 150000,
        "income_unstable": False,
        "anomaly": False,
        "habit_warning": None,
        "behavior_profile": None,
        "pattern_memory": None
    }

    result = generate_insight(analysis_result)

    assert result["risk_level"] == "LOW"
    assert result["insight"]["title"] is not None
    assert isinstance(result["insight"]["patterns"], list)


# ==================================
# 2️⃣ HIGH RISK
# ==================================
def test_generate_insight_high():
    analysis_result = {
        "risk_level": "HIGH",
        "dominant_category": "Entertainment",
        "total_expense": 1200000,
        "income_unstable": True,
        "anomaly": True,
        "habit_warning": {
            "level": "WARNING",
            "message": "Pengeluaran hiburan meningkat."
        },
        "behavior_profile": {
            "summary": "Cenderung impulsif.",
            "spending_style": ["Belanja malam hari"],
            "risk_trait": ["Overspending"]
        },
        "pattern_memory": {
            "expense_trend": "MENINGKAT",
            "notes": ["3 hari terakhir naik."]
        }
    }

    result = generate_insight(analysis_result)

    assert result["risk_level"] == "HIGH"
    assert len(result["insight"]["patterns"]) > 0
    assert result["insight"]["warnings"][0]["level"] == "WARNING"


# ==================================
# 3️⃣ DANGER RISK
# ==================================
def test_generate_insight_danger():
    analysis_result = {
        "risk_level": "DANGER",
        "dominant_category": "Shopping",
        "total_expense": 3000000,
        "income_unstable": True,
        "anomaly": True,
        "habit_warning": {
            "level": "CRITICAL",
            "message": "Pengeluaran tidak terkendali."
        },
        "behavior_profile": None,
        "pattern_memory": None
    }

    result = generate_insight(analysis_result)

    assert result["risk_level"] == "DANGER"
    assert result["insight"]["warnings"][0]["level"] == "CRITICAL"