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
    - Fast path hanya untuk query angka eksplisit
    - Semua pertanyaan lain masuk LLM (Groq)
    """

    # Step 1: Get precomputed insight
    insight = get_latest_insight(user_id)

    # Step 2: Handle missing insight — fallback on-demand
    if not insight:
        try:
            from app.jobs.daily_job import run_daily_job_for_user
            print(f"[INFO] No precomputed insight for {user_id}, running on-demand...")
            run_daily_job_for_user(user_id)
            insight = get_latest_insight(user_id)
        except Exception as e:
            print(f"[WARNING] On-demand analysis failed: {e}")

    if not insight:
        return {
            "mode": "pending",
            "data": None,
            "response": "Belum ada data keuangan. Yuk mulai catat transaksi dulu!"
        }

    context = insight

    # ========================================
    # 🚀 SMART FAST PATH
    # Hanya untuk query angka total yang eksplisit
    # ========================================

    msg = message.lower().strip()

    FAST_PATH_TRIGGERS = [
        "total pengeluaran",
        "total pemasukan",
        "total income",
        "total expense",
        "berapa saldo",
        "saldo sekarang",
        "net cashflow",
        "cashflow bulan",
    ]

    if any(trigger in msg for trigger in FAST_PATH_TRIGGERS):
        balance = int(context.get("net_cashflow", 0) or 0)
        income = int(context.get("total_income", 0) or 0)
        expense = int(context.get("total_expense", 0) or 0)

        def fmt(n: int) -> str:
            return f"Rp {n:,}".replace(",", ".")

        if "saldo" in msg or "balance" in msg or "cashflow" in msg:
            resp = f"Saldo bersih bulan ini: {fmt(balance)}"
        elif "pengeluaran" in msg or "expense" in msg:
            resp = f"Total pengeluaran bulan ini: {fmt(expense)}"
        elif "pemasukan" in msg or "income" in msg:
            resp = f"Total pemasukan bulan ini: {fmt(income)}"
        else:
            resp = f"Saldo: {fmt(balance)} | Pemasukan: {fmt(income)} | Pengeluaran: {fmt(expense)}"

        return {
            "mode": "fast",
            "data": context,
            "response": resp
        }

    # ========================================
    # 🧠 LLM PATH (Groq)
    # Semua pertanyaan selain angka eksplisit
    # termasuk: halo, tips, kategori, saran, dll
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