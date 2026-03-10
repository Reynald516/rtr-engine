# app/conversation/llm_client.py

import os
import logging
from groq import Groq

logging.basicConfig(level=logging.INFO)

_client = None


def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY belum tersedia di environment.")

        _client = Groq(api_key=api_key)

    return _client


def chat_completion(
    messages,
    temperature=0.6,
    max_tokens=250,
    model=None
):
    client = get_client()

    model = model or os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    try:
        logging.info(f"Request ke model: {model}")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if not response.choices:
            return "No response from model."

        return response.choices[0].message.content or ""

    except Exception as e:
        logging.error(f"LLM Error: {str(e)}")
        return f"Error: {str(e)}"