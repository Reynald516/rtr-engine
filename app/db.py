# app/db.py
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE ENV belum lengkap!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_transactions_by_user(user_id: str):
    """
    Fetch semua transaksi untuk user tertentu.
    Return: list of dict [{'amount': ..., 'type': ..., 'category': ...}, ...]
    """
    try:
        response = (
            supabase
            .table("transactions")
            .select("amount, type, category, created_at")
            .eq("user_id", user_id)
            .execute()
        )

        if response.data is None:
            raise RuntimeError("Supabase fetch returned no data")

        data = response.data

        for item in data:
            item["timestamp"] = item.get("created_at")

        return data

    except Exception as e:
        raise RuntimeError(f"Fetch transactions failed: {str(e)}")

def save_user_analysis(data: dict, analysis_date: str):
    """
    Insert hasil analisis user ke table user_analysis.
    Return: list of dict hasil insert
    """
    try:
        response = (
            supabase
            .table("user_analysis")
            .upsert(
                {
                    "user_id": data["user_id"],
                    "analysis_date": analysis_date,
                    "cluster": data["cluster"],
                    "anomaly": data["anomaly"],
                    "risk_level": data["risk_level"],
                    "summary": data["summary"],
                    "dominant_category": data["dominant_category"],
                    "total_expense": data["total_expense"],
                    "total_income": data["total_income"],
                },
                on_conflict="user_id,analysis_date"
            )
            .execute()
        )

        if response.data is None:
            raise RuntimeError("Supabase insert returned no data")

        return response.data

    except Exception as e:
        raise RuntimeError(f"Save user analysis failed: {str(e)}")
    

def fetch_analysis_by_date(user_id: str, target_date: str):
    response = (
        supabase
        .table("user_analysis")
        .select("*")
        .eq("user_id", user_id)
        .eq("analysis_date", target_date)
        .single()
        .execute()
    )

    return response.data

def save_behavior_analysis(data: dict):
    response = (
        supabase
        .table("user_behavior_analysis")
        .upsert(
            data,
            on_conflict="user_id,analysis_date"
        )
        .execute()
    )

    return response.data

def fetch_last_analysis_before_today(user_id):
    
    """
    Ambil analisis terakhir user sebelum tanggal hari ini
    """
    today = date.today().isoformat()

    try:
        # PSEUDO SQL / QUERY STYLE
        # Ambil 1 data terakhir < today
        result = supabase.table("user_analysis") \
            .select("*") \
            .eq("user_id", user_id) \
            .lt("analysis_date", today) \
            .order("analysis_date", desc=True) \
            .limit(1) \
            .execute()

        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        raise RuntimeError(f"Fetch last analysis failed: {str(e)}")
    
def fetch_recent_analyses(user_id: str, days: int = 3):
    """
    Ambil N hari terakhir analisis user (maks 7 untuk MVP)
    """
    try:
        result = (
            supabase
            .table("user_analysis")
            .select("*")
            .eq("user_id", user_id)
            .order("analysis_date", desc=True)
            .limit(days)
            .execute()
        )

        return result.data or []

    except Exception as e:
        raise RuntimeError(f"Fetch recent analyses failed: {str(e)}")