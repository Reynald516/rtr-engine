# app/repositories/insight_repository.py

from datetime import datetime, timezone, date
from app.db import supabase


# =========================================
# PHASE 4 RULE:
# UI MUST ONLY READ FROM user_insights
# NEVER recompute financial or behavioral data at request time
# =========================================


def get_user_insight(user_id: str):
    """
    Query insights table for user.
    Returns dict with patterns, behavior, forecast or None if no data.
    """
    try:
        response = (
            supabase
            .table("insights")
            .select("patterns, behavior, forecast")
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data or len(response.data) == 0:
            return None
        
        row = response.data[0]
        
        # Handle NULL values - convert to empty dict
        patterns = row.get("patterns") if row.get("patterns") is not None else {}
        behavior = row.get("behavior") if row.get("behavior") is not None else {}
        forecast = row.get("forecast") if row.get("forecast") is not None else {}
        
        return {
            "patterns": patterns,
            "behavior": behavior,
            "forecast": forecast
        }
    
    except Exception:
        return None


def save_user_insight(user_id: str, data: dict):
    """
    Upsert user insight into insights table.
    Fields: user_id, patterns, behavior, forecast, updated_at
    """
    try:
        insight_data = data.get("insight", {})
        
        response = (
            supabase
            .table("insights")
            .upsert(
                {
                    "user_id": user_id,
                    "patterns": insight_data.get("patterns", []),
                    "behavior": insight_data.get("behavior", {}),
                    "forecast": insight_data.get("forecast", {}),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                on_conflict="user_id"
            )
            .execute()
        )
        
        return response.data
    
    except Exception:
        return None


# =========================================
# PHASE 4: PRECOMPUTED INSIGHT FUNCTIONS
# Store and retrieve financial insights for instant UI loading
# =========================================

def save_user_financial_insight(user_id: str, insight: dict):
    """
    Save comprehensive financial insight to user_insights table.
    This is called AFTER daily job generates insights.
    UI should read from this table - NEVER recompute at request time.
    
    Args:
        user_id: The user's ID
        insight: Dict containing analysis results from FinancialAnalyzer
    """
    try:
        today = str(date.today())
        
        # Map analysis result to database fields
        supabase.rpc("upsert_user_insight", {
            "p_user_id": user_id,
            "p_date": today,
            "p_income": insight.get("total_income", 0),
            "p_expense": insight.get("total_expense", 0),
            "p_cashflow": insight.get("net_cashflow", 0),
            "p_category": insight.get("dominant_category"),
            "p_largest": insight.get("largest_expense", 0),
            "p_pattern": insight.get("pattern_memory"),
            "p_anomaly": insight.get("is_anomaly", False),
            "p_risk": insight.get("risk_level"),
            "p_summary": insight.get("behavior_profile"),
            "p_recommendation": insight.get("habit_warning"),
        }).execute()
        
    except Exception as e:
        # Log error but don't crash - daily job should continue
        print(f"[WARNING] Failed to save financial insight for {user_id}: {e}")


def get_latest_insight(user_id: str):
    """
    Fetch latest precomputed insight for user.
    This is the FAST path for UI - no recomputation needed.
    
    Returns:
        dict: Latest insight data or None if not found
    """
    try:
        res = (
            supabase
            .table("user_insights")
            .select("*")
            .eq("user_id", user_id)
            .order("insight_date", desc=True)
            .limit(1)
            .execute()
        )

        if res.data:
            return res.data[0]

        return None
    
    except Exception:
        return None


def get_user_insights_history(user_id: str, days: int = 30):
    """
    Fetch historical insights for user.
    Useful for trend analysis and charts.
    
    Args:
        user_id: The user's ID
        days: Number of days to look back (default 30)
    
    Returns:
        list: List of insight records
    """
    try:
        res = (
            supabase
            .table("user_insights")
            .select("*")
            .eq("user_id", user_id)
            .order("insight_date", desc=True)
            .limit(days)
            .execute()
        )

        return res.data if res.data else []
    
    except Exception:
        return []
