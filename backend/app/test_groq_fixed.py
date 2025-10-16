# test_groq_fixed.py
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv('../../.env')

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": "Say hello in Spanish"}],
        model="llama3-8b-8192",  # Updated model
    )
    print("✅ Groq API is working!")
    print(f"Response: {chat_completion.choices[0].message.content}")
except Exception as e:
    print(f"❌ Groq API error: {e}")