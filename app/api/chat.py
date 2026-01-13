from app.db import fetch_transactions_by_user
from app.insight_router import route_insight
from app.insight_prompt import build_system_prompt
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_user(user_id: str, user_message: str):
    # 1. Ambil transaksi
    transactions = fetch_transactions_by_user(user_id)

    if not transactions:
        return "Data transaksi kamu belum ada. Mulai catat dulu ya."

    # 2. MOCK engine_output (nanti hasil real engine)
    engine_output = {
        "insights": [
            {"type": "PATTERN_MEMORY"}
        ]
    }

    # 3. Tentukan mode bicara
    route = route_insight(engine_output)

    # 4. Build system prompt RTR
    system_prompt = build_system_prompt(
        mode=route["mode"],
        goal=route["goal"],
        context={
            "summary": "Pengeluaran makan cukup dominan",
            "risk_level": "sedang",
            "dominant_category": "makanan"
        }
    )

    # 5. Panggil OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"DATA TRANSAKSI USER:\n{transactions}"},
            {"role": "user", "content": user_message},
        ]
    )

    return response.choices[0].message.content