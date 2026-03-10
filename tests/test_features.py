# tests/test_features.py

import pandas as pd
import pytest

from app.features import extract_features, extract_daily_features


# ===============================
# 1️⃣ Normal Case
# ===============================
def test_extract_features_normal():
    data = pd.DataFrame([
        {"type": "income", "amount": 1000, "timestamp": "2025-01-01 10:00:00", "category": "salary"},
        {"type": "expense", "amount": 200, "timestamp": "2025-01-01 22:00:00", "category": "food"},
        {"type": "expense", "amount": 100, "timestamp": "2025-01-02 14:00:00", "category": "entertainment"},
    ])

    result = extract_features(data)

    assert result["total_income"] == 1000
    assert result["total_expense"] == 300
    assert result["food_ratio"] == 200 / 300
    assert result["entertainment_ratio"] == 100 / 300
    assert result["night_ratio"] == 200 / 300


# ===============================
# 2️⃣ Empty DataFrame
# ===============================
def test_extract_features_empty():
    df = pd.DataFrame(columns=["type", "amount", "timestamp", "category"])

    result = extract_features(df)

    assert result["total_income"] == 0
    assert result["total_expense"] == 0
    assert result["night_ratio"] == 0


# ===============================
# 3️⃣ Only Income
# ===============================
def test_extract_features_only_income():
    df = pd.DataFrame([
        {"type": "income", "amount": 500, "timestamp": "2025-01-01 10:00:00", "category": "salary"},
    ])

    result = extract_features(df)

    assert result["total_income"] == 500
    assert result["total_expense"] == 0
    assert result["food_ratio"] == 0


# ===============================
# 4️⃣ Missing Timestamp
# ===============================
def test_extract_features_missing_timestamp():
    df = pd.DataFrame([
        {"type": "income", "amount": 500, "category": "salary"},
    ])

    with pytest.raises(ValueError):
        extract_features(df)


# ===============================
# 5️⃣ Daily Features Normal
# ===============================
def test_extract_daily_features_normal():
    df = pd.DataFrame([
        {"type": "expense", "amount": 100, "timestamp": "2025-01-01 22:00:00", "category": "food"},
        {"type": "expense", "amount": 50, "timestamp": "2025-01-01 10:00:00", "category": "entertainment"},
    ])

    result = extract_daily_features(df)

    assert len(result) == 1
    assert result.iloc[0]["total_spend"] == 150
    assert result.iloc[0]["night_ratio"] == 100 / 150


# ===============================
# 6️⃣ Daily Features Empty
# ===============================
def test_extract_daily_features_empty():
    df = pd.DataFrame(columns=["type", "amount", "timestamp", "category"])

    result = extract_daily_features(df)

    assert result.empty