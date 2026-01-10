# app/features.py
import pandas as pd

def extract_features(transactions: pd.DataFrame):
    df = transactions.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    daily_total = df.groupby('date')['amount'].sum()
    total_spend = daily_total.sum()
    
    # night = jam 21:00 - 05:00
    night_spend = df[(df['timestamp'].dt.hour >= 21) | (df['timestamp'].dt.hour <= 5)]['amount'].sum()
    
    # kategori
    food_spend = df[df['category'] == 'food']['amount'].sum()
    entertainment_spend = df[df['category'] == 'entertainment']['amount'].sum()
    
    features = {
        "avg_daily_spend": daily_total.mean(),
        "spending_std": daily_total.std(),
        "night_ratio": night_spend / total_spend if total_spend else 0,
        "food_ratio": food_spend / total_spend if total_spend else 0,
        "entertainment_ratio": entertainment_spend / total_spend if total_spend else 0,
        "transaction_count_per_day": df.groupby('date').size().mean()
    }
    return features