# app/insights/schema.py

def build_insight_response(
    analysis_date,
    risk_level,
    title,
    summary,
    patterns,
    warnings,
    advice
):
    return {
        "analysis_date": analysis_date,
        "risk_level": risk_level,
        "insight": {
            "title": title,
            "summary": summary,
            "patterns": patterns,
            "warnings": warnings,
            "advice": advice
        }
    }