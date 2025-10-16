# test_groq.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": "Say hello in Spanish"}],
        model="gemma2-9b-it",
    )
    print("✅ Groq API is working!")
    print(f"Response: {chat_completion.choices[0].message.content}")
except Exception as e:
    print(f"❌ Groq API error: {e}")