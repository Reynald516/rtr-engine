import os
from openai import OpenAI
from app.conversation.insight_router import route_insight
from app.conversation.insight_prompt import build_system_prompt
from app.conversation.memory import get_memory, save_message

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def generate_user_message(engine_output: dict) -> dict:
    # route_insight SEKARANG DIANGGAP RETURN STRING MODE
    mode = route_insight(engine_output)

    # MVP goal mapping (simple & aman)
    if mode == "WARNING":
        goal = "Buat user sadar tanpa menghakimi"
    elif mode == "RISK":
        goal = "Bantu user refleksi dan hati-hati"
    else:
        goal = "Bantu user memahami kondisi keuangannya"

    system_prompt = build_system_prompt(
        mode=mode,
        goal=goal
    )

    user_payload = {
        "engine_insights": engine_output.get("insights", {}),
        "summary": engine_output.get("summary", "")
    }

    return {
        "system_prompt": system_prompt,
        "user_payload": user_payload
    }

def talk_to_user(engine_output: dict) -> str:
    payload = generate_user_message(engine_output)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": payload["system_prompt"]},
            {
                "role": "user",
                "content": f"""
Ringkasan kondisi user:
{payload['user_payload']['summary']}

Insight mesin:
{payload['user_payload']['engine_insights']}
"""
            }
        ],
        temperature=0.6,
        max_tokens=250
    )

    return response.choices[0].message.content

def chat_with_user(user_id: str, user_message: str, engine_context: dict) -> str:
    memory = get_memory(user_id)

    messages = [
        {"role": "system", "content": engine_context["system_prompt"]}
    ]

    messages.extend(memory)

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.6,
        max_tokens=250
    )

    assistant_reply = response.choices[0].message.content

    # SIMPAN MEMORY
    save_message(user_id, "user", user_message)
    save_message(user_id, "assistant", assistant_reply)

    return assistant_reply