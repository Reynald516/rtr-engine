# app/engine/scheduled_engine.py

from app.db import supabase


def run_scheduled_analysis(user_id: str, analysis_result: dict):
    """
    Run heavy analysis (pattern, behavior) and store results.
    Designed for cron job.
    """
    
    insights = []
    
    # Example: spending pattern
    total_expense = analysis_result.get("total_expense", 0)
    total_income = analysis_result.get("total_income", 0)
    
    if total_expense > 5000000:
        insights.append({
            "type": "high_spending",
            "value": {"amount": total_expense}
        })
    
    # Check if income less than expense
    if total_income > 0 and total_expense > total_income:
        insights.append({
            "type": "overspending",
            "value": {"expense": total_expense, "income": total_income}
        })
    
    # Check dominant category
    dominant_category = analysis_result.get("dominant_category")
    if dominant_category:
        insights.append({
            "type": "dominant_category",
            "value": {"category": dominant_category}
        })
    
    # Save to DB - upsert into insights table
    for ins in insights:
        try:
            supabase.table("insights").upsert({
                "user_id": user_id,
                "insight_type": ins["type"],
                "value": ins["value"]
            }).execute()
        except Exception:
            # Skip failed inserts, continue with others
            continue
    
    return {"status": "completed", "insights_count": len(insights)}
