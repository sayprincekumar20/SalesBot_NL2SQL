import json
import logging
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def summarize_data(user_query: str, rows: list[dict]) -> str | None:
    """Summarize up to first 200 rows compactly."""
    if not rows:
        return "No rows returned."

    sample = rows[:200]  # cap to avoid huge prompts
    try:
        messages = [
            {"role": "system", "content": "You summarize analytical SQL results briefly and clearly for business users."},
            {"role": "user", "content": f"User question: {user_query}\n\nData (JSON rows, truncated):\n{json.dumps(sample)[:6000]}\n\nWrite 3-5 concise bullet points highlighting the key insights. Avoid restating raw rows; compute relevant totals or top items if obvious."}
        ]
        chat = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=messages,
            temperature=0.2
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"[SUMMARY ERROR] {e}")
        return None
