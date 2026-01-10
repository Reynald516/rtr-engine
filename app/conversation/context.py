# app/conversation/context.py

engine_context_store = {}

def save_engine_context(user_id: str, context: dict):
    engine_context_store[user_id] = context

def get_engine_context(user_id: str):
    return engine_context_store.get(user_id)