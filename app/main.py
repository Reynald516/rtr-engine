# app/main.py
from fastapi import FastAPI, HTTPException
import pandas as pd
from datetime import date, timedelta
from app.db import fetch_last_analysis_before_today
from app.behavior.evolution import evaluate_evolution
from app.db import fetch_recent_analyses
from app.behavior.pattern_memory import analyze_pattern_memory
from app.behavior.profile import build_behavior_profile
from app.behavior.habit_warning import detect_habit_warning
from app.conversation.talker import talk_to_user
from app.conversation.talker import chat_with_user
from app.conversation.insight_prompt import build_system_prompt
from app.conversation.context import save_engine_context
from app.conversation.context import get_engine_context
from app.clustering import cluster_user
from app.anomaly import detect_anomaly
from app.logic import rtr_logic
from app.features import extract_features, extract_daily_features

from app.db import (
    fetch_transactions_by_user,
    save_user_analysis,
    fetch_analysis_by_date,
    save_behavior_analysis
)
from app.behavior.comparator import compare_behavior
from app.insights.generator import generate_insight

app = FastAPI(title="RTR Engine", version="0.1.0")


@app.get("/")
def root():
    return {"message": "RTR Engine is running"}


@app.post("/analyze_user")
def analyze_user(user_id: str):
    # === FETCH TRANSAKSI ===
    try:
        transactions = fetch_transactions_by_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not transactions:
        raise HTTPException(status_code=404, detail="User / transaksi tidak ditemukan")

    df = pd.DataFrame(transactions)

    features = extract_features(df)
    features_df = pd.DataFrame([features])

    daily_features = extract_daily_features(df)

    cluster_cols = [
        "total_spend",
        "transaction_count",
        "night_ratio",
        "food_ratio",
        "entertainment_ratio"
    ]
    
    # === DAILY CLUSTERING (SAFE) ===
    if daily_features.empty or daily_features.shape[0] < 3:
        clusters = None
    else:
        clusters, model = cluster_user(
            daily_features[cluster_cols],
            n_clusters=3
        )
        
        if clusters is not None:
            daily_features["cluster"] = clusters

    # === USER CLUSTER DARI DAILY BEHAVIOR ===
    if "cluster" in daily_features.columns:
        user_cluster = int(daily_features["cluster"].mode()[0])
    else:
        user_cluster = 0

    required_cols = {"amount", "type", "category"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(status_code=400, detail="Struktur transaksi tidak valid")

    df["type"] = df["type"].str.lower()

    income_df = df[df["type"] == "income"]
    expense_df = df[df["type"] == "expense"]

    expense_series = expense_df["amount"]
    anomaly_flag = detect_anomaly(expense_series)
    is_anomaly = -1 in anomaly_flag

    total_income = int(income_df["amount"].sum())
    total_expense = int(expense_df["amount"].sum())

    dominant_category = (
        expense_df["category"].value_counts().idxmax()
        if not expense_df.empty else None
    )

    total_flow = total_income + total_expense
    expense_ratio = total_expense / total_flow if total_flow > 0 else 0

    risk_level = rtr_logic(
        cluster=user_cluster,
        anomaly_flag=anomaly_flag,
        night_ratio=features["night_ratio"]
    )

    analysis = {
        "user_id": user_id,
        "cluster": user_cluster,
        "anomaly": is_anomaly,
        "risk_level": risk_level,
        "summary": f"Total pengeluaran {total_expense}, kategori dominan {dominant_category}",
        "dominant_category": dominant_category,
        "total_expense": total_expense,
        "total_income": total_income
    }

    # === CORE ENGINE LOGIC ===
    try:
        # 1. Simpan snapshot hari ini
        save_user_analysis(analysis)

        today_date = date.today().isoformat()
        
        previous_analysis = fetch_last_analysis_before_today(
            user_id=user_id,
            today=today_date
        )
        
        evolution = None
        if previous_analysis:
            evolution = evaluate_evolution(
                today={
                    "total_expense": total_expense,
                    "risk_level": risk_level,
                    "dominant_category": dominant_category
                },
                previous=previous_analysis
            )

        # 2. Ambil data kemarin
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        try:
            yesterday_analysis = fetch_analysis_by_date(user_id, yesterday)
        except:
            yesterday_analysis = None

        # 3. Bandingkan perilaku jika ada data kemarin
        if yesterday_analysis:
            behavior = compare_behavior(
                today={
                    "total_expense": total_expense,
                    "total_income": total_income,
                    "risk_level": risk_level
                },
                yesterday=yesterday_analysis
            )

            save_behavior_analysis({
                "user_id": user_id,
                "analysis_date": date.today().isoformat(),
                **behavior
            })

        # === PATTERN MEMORY (v1.3) ===
        recent_analyses = fetch_recent_analyses(user_id=user_id, days=3)
        
        pattern_memory = None
        if recent_analyses and len(recent_analyses) >= 2:
            pattern_memory = analyze_pattern_memory(recent_analyses)

        # === HABIT WARNING (v1.5) ===
        habit_warning = detect_habit_warning(
            pattern_memory=pattern_memory,
            dominant_category=dominant_category
        )

        # === BEHAVIOR PROFILE (v1.4) ===
        behavior_profile = build_behavior_profile(
            total_income=total_income,
            total_expense=total_expense,
            risk_level=risk_level,
            dominant_category=dominant_category,
            pattern_memory=pattern_memory
        )

        # 4. Generate AI Insight (LAST STEP)
        insight = generate_insight({
            **analysis,
            "evolution": evolution,
            "pattern_memory": pattern_memory,
            "behavior_profile": behavior_profile,
            "habit_warning": habit_warning
        })

        save_engine_context(user_id, {
            "risk_level": risk_level,
            "dominant_category": dominant_category,
            "summary": insight["insight"]["summary"],
            "patterns": insight["insight"]["patterns"]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "analysis": analysis,
        "insight": insight,
    }

from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str
    transactions: Optional[List[dict]] = None

@app.post("/chat")
def chat(payload: ChatRequest):
    user_id = payload.user_id
    message = payload.message
    try:
        context = get_engine_context(user_id)

        # === AUTO ANALYZE JIKA BELUM ADA CONTEXT ===
        if not context:
            analyze_user(user_id)
            context = get_engine_context(user_id)

            if not context:
                raise HTTPException(
                    status_code=500,
                    detail="Engine gagal membangun context user."
                )

        system_prompt = build_system_prompt(
            mode="coach",
            goal="financial awareness",
            context=context
        )

        reply = chat_with_user(
            user_id=user_id,
            user_message=message,
            engine_context={
                "system_prompt": system_prompt
            }
        )

        return {"answer": reply}

    except HTTPException:
        raise
    except Exception as e:
        context = get_engine_context(user_id)
        
        if context:
            return {
                "answer": (
                    "Saya mungkin tidak bisa ngobrol panjang sekarang, "
                    "tapi dari analisa terakhir yang ada:\n\n"
                    f"- Risk level kamu: {context.get('risk_level')}\n"
                    f"- Pengeluaran dominan: {context.get('dominant_category')}\n\n"
                    "Kalau kamu mau, kita bisa bahas pelan-pelan dari situ."
                ),
                "mode": "fallback"
            }
        
        raise HTTPException(
            status_code=503,
            detail="Chat service sementara tidak tersedia."
        )