# app/main.py

# PHASE 4 HARD RULE:
# API must NEVER trigger analysis or insight generation
# Only read from user_insights table
# All insights must be precomputed by daily_job

from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.repositories.insight_repository import get_latest_insight
from app.engine.engine_pipeline import run_pipeline

app = FastAPI(title="RTR Engine", version="0.1.0")


@app.get("/")
def root():
    return {"message": "RTR Engine is running"}


def run_analysis(user_id: str):
    """
    PHASE 4: Read ONLY from precomputed user_insights table.
    Never run analyzer or generate insight at request time.
    """
    # PHASE 4: Get precomputed insight directly
    insight_data = get_latest_insight(user_id)
    
    if insight_data is None:
        raise HTTPException(status_code=404, detail="Insight belum tersedia")
    
    return {
        "status": "success",
        "insight": insight_data,
        "context": insight_data
    }


@app.post("/analyze_user")
def analyze_user(user_id: str):
    try:
        return run_analysis(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat(payload: ChatRequest):
    user_id = payload.user_id
    message = payload.message
    
    try:
        # PHASE 4: Use run_pipeline (read-only, no recompute)
        result = run_pipeline(user_id, message)
        
        return result

    except Exception as e:
        return {
            "mode": "error",
            "data": None,
            "response": f"Maaf, terjadi kesalahan: {str(e)}"
        }


def is_context_stale(context: dict) -> bool:
    if not context or "timestamp" not in context:
        return True

    try:
        timestamp = datetime.fromisoformat(context["timestamp"])
    except Exception:
        return True

    return datetime.now(timezone.utc) - timestamp > timedelta(days=7)


# ==============================
# ORCHESTRATOR ENDPOINTS
# ==============================

@app.get("/run-daily/{user_id}")
async def run_daily(user_id: str):
    """
    PHASE 4: Return precomputed insight directly.
    Daily analysis runs via daily_job - this endpoint just returns cached data.
    """
    insight = get_latest_insight(user_id)
    
    if not insight:
        return {
            "status": "pending",
            "message": "Insight belum tersedia. Daily job mungkin belum berjalan."
        }
    
    return {
        "status": "success",
        "insight": insight
    }
