# app/conversation/memory.py

# memory sederhana (RAM)
conversation_memory = {}

def get_memory(user_id: str):
    return conversation_memory.get(user_id, [])

def save_message(user_id: str, role: str, content: str):
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    conversation_memory[user_id].append({
        "role": role,
        "content": content
    })

    # BATASI 6 pesan terakhir (biar murah & stabil)
    conversation_memory[user_id] = conversation_memory[user_id][-6:]