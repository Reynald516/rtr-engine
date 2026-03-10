# app/engine/engine_pipeline.py

# PHASE 4 HARD RULE:
# NEVER run analyzer or generate insight at request time
# ONLY read from user_insights table
# All insights must be precomputed by daily_job

from datetime import datetime
from app.conversation.talker import chat_with_user
from app.repositories.insight_repository import get_latest_insight
from app.db import supabase


# ⚠️ DEPRECATED FUNCTION
# PHASE 4 RULE: DO NOT USE THIS IN PIPELINE OR API
# ONLY user_insights is allowed as source of truth
# This function is kept ONLY for internal/debugging purposes
def get_monthly_financial_summary(user_id: str) -> dict:
    """
    Fetch precomputed financial summary from user_financial_summary table.
    
    Input: user_id
    Query: user_financial_summary for current month
    Output: Financial summary dict
    Raises: RuntimeError if not found
    """
    # =====================================================
    # ⚠️ HARD GUARD: PHASE 4 VIOLATION
    # =====================================================
    raise RuntimeError("PHASE 4 VIOLATION: Do not use user_financial_summary in request pipeline")
    
    current_month = datetime.now().strftime("%Y-%m")
    
    try:
        response = (
            supabase
            .table("user_financial_summary")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", current_month)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # No silent fallback - raise error to detect missing data
        raise RuntimeError(f"Financial summary not found for user {user_id}")
    
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to fetch financial summary: {str(e)}")


def run_pipeline(user_id: str, message: str) -> dict:
    """
    PHASE 4 + PHASE 5 PREPARATION

    Rules:
    - NEVER compute insight here
    - ONLY read from user_insights
    - Add basic router (fast vs llm)
    """

    # Step 1: Get precomputed insight
    insight = get_latest_insight(user_id)

    # Step 2: Handle missing insight
    if not insight:
        return {
            "mode": "pending",
            "data": None,
            "response": "Data sedang diproses, coba lagi nanti"
        }

    context = insight

    # ========================================
    # 🚀 BASIC ROUTER (PHASE 5 PREP)
    # ========================================

    msg = message.lower().strip()

    # ========================================
    # 🚀 SMART FAST PATH (PHASE 5 v1)
    # ========================================

    # Financial quick queries
    if any(keyword in msg for keyword in [
        "saldo",
        "pengeluaran",
        "penghasilan",
        "income",
        "expense",
        "balance"
    ]):
        # FIX: Use net_cashflow (matching insight_repository field name)
        balance = context.get("net_cashflow", 0)
        income = context.get("total_income", 0)
        expense = context.get("total_expense", 0)
        
        # Context-aware response based on keyword
        if "saldo" in msg or "balance" in msg:
            response = f"Saldo bulan ini: {balance}"
        elif "pengeluaran" in msg or "expense" in msg:
            response = f"Total pengeluaran bulan ini: {expense}"
        elif "penghasilan" in msg or "income" in msg:
            response = f"Total pemasukan bulan ini: {income}"
        else:
            response = f"Saldo: {balance}. Income: {income}. Expense: {expense}"
        
        return {
            "mode": "fast",
            "data": context,
            "response": response
        }

    # Short generic messages
    if len(msg) < 20:
        return {
            "mode": "fast",
            "data": context,
            "response": "Oke, diproses cepat oleh sistem"
        }

    # ========================================
    # 🧠 LLM PATH
    # ========================================
    response = chat_with_user(
        user_id=user_id,
        user_message=message,
        context=context
    )

    return {
        "mode": "llm",
        "data": insight,
        "response": response
    }
