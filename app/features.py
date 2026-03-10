# app/features.py
import pandas as pd

# =====================================================
# SINGLE USER SUMMARY FEATURES (BEHAVIOR ONLY)
# SQL handles ALL financial aggregation
# =====================================================
def extract_features(transactions: pd.DataFrame, financial_data: dict = None):
    """
    Extract behavior metrics only.
    Financial totals MUST come from SQL (passed via financial_data).
    """
    df = transactions.copy()

    # === BASIC CLEANING ===
    df = df[df["amount"] > 0]

    # =========================
    # SAFE TIMESTAMP HANDLING
    # =========================
    if "timestamp" not in df.columns:
        raise ValueError("Timestamp column required")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # =========================
    # FINANCIAL DATA (FROM SQL)
    # =========================
    # If financial_data provided, use it. Otherwise use safe defaults.
    if financial_data:
        total_income = financial_data.get("total_income", 0)
        total_expense = financial_data.get("total_expense", 0)
    else:
        # Fallback: calculate but mark as deprecated
        # TODO: Remove this fallback after full migration
        total_income = 0
        total_expense = 0
    
    total_spend = total_expense

    # =========================
    # NIGHT SPENDING (BEHAVIOR)
    # =========================
    night_spend = df[
        (df["type"] == "expense") &
        (
            (df["timestamp"].dt.hour >= 21) |
            (df["timestamp"].dt.hour <= 5)
        )
    ]["amount"].sum()

    # =========================
    # DAILY BEHAVIOR
    # =========================
    expense_df = df[df["type"] == "expense"]

    if not expense_df.empty:
        daily_total = expense_df.groupby("date")["amount"].sum()
        avg_daily_spend = daily_total.mean()
        spending_std = daily_total.std()
        tx_per_day = expense_df.groupby("date").size().mean()
    else:
        avg_daily_spend = 0
        spending_std = 0
        tx_per_day = 0

    # =========================
    # CATEGORY RATIOS (BEHAVIOR)
    # =========================
    category_spend = (
        expense_df.groupby("category")["amount"].sum()
    )

    if total_spend > 0:
        category_ratios = (category_spend / total_spend).to_dict()
    else:
        category_ratios = {}

    result = {
        # Financial data from SQL (passed through)
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        # Behavior metrics only
        "avg_daily_spend": float(avg_daily_spend),
        "spending_std": float(spending_std) if spending_std else 0,
        "night_ratio": night_spend / total_spend if total_spend else 0,
        "category_ratios": category_ratios,
        "transaction_count_per_day": float(tx_per_day),
    }
    
    for category, ratio in category_ratios.items():
        result[f"{category}_ratio"] = ratio
    
    common_categories = ["food", "entertainment", "transportation", "shopping", "bills"]
    for cat in common_categories:
        if f"{cat}_ratio" not in result:
            result[f"{cat}_ratio"] = 0.0
    
    return result


# =====================================================
# DAILY FEATURES (KHUSUS CLUSTERING & ML)
# =====================================================
def extract_daily_features(transactions: pd.DataFrame):
    """
    Extract daily features for clustering and ML.
    No financial aggregation - pure behavioral patterns.
    """
    df = transactions.copy()

    # === CLUSTERING = EXPENSE ONLY ===
    df = df[df["type"] == "expense"]
    df = df[df["amount"] > 0]

    if df.empty:
        return pd.DataFrame()

    # === TIMESTAMP ===
    if "timestamp" not in df.columns:
        raise ValueError("Timestamp column required")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    daily_features = []

    for date, day_df in df.groupby("date"):
        total_spend = day_df["amount"].sum()

        night_spend = day_df[
            (day_df["timestamp"].dt.hour >= 21) |
            (day_df["timestamp"].dt.hour <= 5)
        ]["amount"].sum()

        category_spend = day_df.groupby("category")["amount"].sum().to_dict()
        
        daily_features.append({
            "date": date,
            "total_spend": total_spend,
            "transaction_count": len(day_df),
            "night_ratio": night_spend / total_spend if total_spend else 0,
            "category_spend": category_spend,
        })

    return pd.DataFrame(daily_features)
