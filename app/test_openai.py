# app/test_openai.py

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

res = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "test"}]
)

print(res.choices[0].message.content)
