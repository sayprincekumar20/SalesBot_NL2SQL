# import os
# import json
# import logging
# from groq import Groq
# from dotenv import load_dotenv

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY not found. Please set it in your .env file.")

# client = Groq(api_key=GROQ_API_KEY)


# def summarize_data(prompt: str, data: list, chart_type: str) -> str:
#     """
#     Generate a natural language summary of the SQL result set.
#     """
#     if not data:
#         return "No data available to summarize."

#     try:
#         # Keep only top rows (avoid overloading LLM with huge dataset)
#         preview = data[:10]
#         user_context = {
#             "user_query": prompt,
#             "chart_type": chart_type,
#             "data_preview": preview,
#             "total_rows": len(data)
#         }

#         system_prompt = """
#         You are a data analyst assistant.
#         Given a SQL query result, summarize the findings clearly in 2–3 sentences.
#         - Be concise and clear.
#         - Highlight patterns, trends, or top items.
#         - Mention total rows if relevant.
#         """

#         chat_completion = client.chat.completions.create(
#             model="gemma2-9b-it",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": json.dumps(user_context)}
#             ],
#             temperature=0.4
#         )

#         summary = chat_completion.choices[0].message.content.strip()
#         return summary

#     except Exception as e:
#         logging.error(f"[SUMMARY ERROR] {e}")
#         return f"Summary unavailable (error: {e})"



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
