# test_llama_model.py
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv('../../.env')

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    print("Testing model: llama-3.1-70b-versatile")
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": "Say hello in Spanish"}],
        model="llama-3.1-70b-versatile",
        temperature=0,
        max_tokens=100
    )
    print("✅ llama-3.1-70b-versatile WORKS!")
    print(f"Response: {chat_completion.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error with llama-3.1-70b-versatile: {e}")
    print(f"Full error details: {vars(e) if hasattr(e, '__dict__') else 'No details'}")