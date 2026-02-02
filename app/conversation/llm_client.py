import os
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def chat_completion(
    messages,
    temperature=0.6,
    max_tokens=250,
    model="llama-3.1-8b-instant"
):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content