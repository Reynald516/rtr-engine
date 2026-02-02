# app/features.py
import pandas as pd

# =====================================================
# SINGLE USER SUMMARY FEATURES (UNTUK ENGINE LOGIC)
# =====================================================
def extract_features(transactions: pd.DataFrame):
    df = transactions.copy()

    # === BASIC CLEANING ===
    df["type"] = df["type"].str.lower()
    df = df[df["amount"] > 0]

    # =========================
    # SAFE TIMESTAMP HANDLING
    # =========================
    if "timestamp" not in df.columns:
        df["timestamp"] = pd.Timestamp.now()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # =========================
    # BASIC TOTALS
    # =========================
    total_income = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    total_spend = total_expense

    # =========================
    # NIGHT SPENDING
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
    # CATEGORY RATIOS
    # =========================
    food_spend = expense_df[expense_df["category"] == "food"]["amount"].sum()
    entertainment_spend = expense_df[expense_df["category"] == "entertainment"]["amount"].sum()

    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "avg_daily_spend": float(avg_daily_spend),
        "spending_std": float(spending_std) if spending_std else 0,
        "night_ratio": night_spend / total_spend if total_spend else 0,
        "food_ratio": food_spend / total_spend if total_spend else 0,
        "entertainment_ratio": entertainment_spend / total_spend if total_spend else 0,
        "transaction_count_per_day": float(tx_per_day),
    }


# =====================================================
# DAILY FEATURES (KHUSUS CLUSTERING & ML)
# =====================================================
def extract_daily_features(transactions: pd.DataFrame):
    df = transactions.copy()

    # === CLUSTERING = EXPENSE ONLY ===
    df["type"] = df["type"].str.lower()
    df = df[df["type"] == "expense"]
    df = df[df["amount"] > 0]

    if df.empty:
        return pd.DataFrame()

    # === TIMESTAMP ===
    if "timestamp" not in df.columns:
        df["timestamp"] = pd.Timestamp.now()

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

        food_spend = day_df[day_df["category"] == "food"]["amount"].sum()
        entertainment_spend = day_df[day_df["category"] == "entertainment"]["amount"].sum()

        daily_features.append({
            "date": date,
            "total_spend": total_spend,
            "transaction_count": len(day_df),
            "night_ratio": night_spend / total_spend if total_spend else 0,
            "food_ratio": food_spend / total_spend if total_spend else 0,
            "entertainment_ratio": entertainment_spend / total_spend if total_spend else 0,
        })

    return pd.DataFrame(daily_features)