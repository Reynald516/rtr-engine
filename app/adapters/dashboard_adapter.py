# app/adapters/dashboard_adapter.py

from datetime import date, timedelta
from app.db import (
    fetch_transactions_by_user,
    save_user_analysis,
    fetch_analysis_by_date,
    save_behavior_analysis,
    fetch_last_analysis_before_today,
    fetch_recent_analyses,
)


def load_transactions(user_id: str):
    return fetch_transactions_by_user(user_id)


def save_analysis_snapshot(data: dict):
    today = date.today().isoformat()
    return save_user_analysis(data, today)


def load_previous_snapshot(user_id: str):
    today = date.today().isoformat()
    return fetch_last_analysis_before_today(user_id, today)


def load_yesterday_snapshot(user_id: str):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return fetch_analysis_by_date(user_id, yesterday)


def save_behavior_snapshot(data: dict):
    return save_behavior_analysis(data)


def load_recent_snapshots(user_id: str, days: int = 3):
    return fetch_recent_analyses(user_id=user_id, days=days)