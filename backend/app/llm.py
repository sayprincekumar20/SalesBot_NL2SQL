import os
import re
import json
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename="llm_sql.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found. Please set it in your .env file.")

client = Groq(api_key=GROQ_API_KEY)


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        # remove leading language tag if present
        t = re.sub(r'^\s*(json|sql)\s*', '', t, flags=re.IGNORECASE)
    return t.strip()


def generate_plan(
    user_query: str,
    schema: str,
    schema_dict: dict,
    relationships: list[dict],
    date_ranges: dict | None = None
) -> dict | None:
    """
    Ask the LLM to decide:
      - intent: "historical" or "forecast"
      - chart_type: "line" | "bar" | "pie" | "table"
      - sql: single-line SQLite SELECT (not executed here)
    Returns Python dict or None on failure.
    """
    rel_text = "\n".join(
        f"- {r['from_table']}.{r['from_col']} = {r['to_table']}.{r['to_col']}"
        for r in relationships
    )

    # NOTE: encodes important Northwind facts to reduce post-fixing
    system_prompt = f"""
You are an assistant that interprets sales queries for the SQLite Northwind database and produces an execution plan in strict JSON.

You will be given:
- A user query
- The database schema (tables and columns)
- Known foreign-key style relationships
- Optional min/max date ranges
- A list of table->columns mapping (schema_dict) for validation

YOUR OUTPUT MUST BE VALID JSON with keys:
- "intent": "historical" or "forecast" (use "forecast" when user asks prediction/next/future)
- "chart_type": one of "line", "bar", "pie", "table"
- "sql": a single-line SQLite SELECT that retrieves the needed HISTORICAL data only

Chart Type Guidelines:
- "pie": proportions of a whole (e.g., sales by category)
- "bar": compare categories (e.g., top products, sales by region)
- "line": time trends (e.g., monthly sales)
- "table": raw listings

IMPORTANT model knowledge and constraints:
1) Table names with spaces MUST be in double quotes, e.g., "Order Details".
2) "Order Details" does NOT have CustomerID; join Customers -> Orders -> Order Details:
   Customers.CustomerID = Orders.CustomerID and Orders.OrderID = "Order Details".OrderID.
3) Discount is a REAL in [0,1]; Sales = Quantity * UnitPrice * (1 - Discount).
4) Prefer existing FKs and provided relationships for JOINs; do not invent columns.
5) Always assign short aliases to tables (e.g., Orders AS o, "Order Details" AS od, Customers AS c).
   After assigning an alias, NEVER reference the raw table name again — always use the alias.
   ❌ Wrong: Orders.OrderDate
   ✅ Correct: o.OrderDate
6) The column "UnitPrice" exists ONLY in "Order Details".
   ❌ Wrong: o.UnitPrice
   ✅ Correct: od.UnitPrice   
7) SQLite only. No unsupported functions (DATEADD, GETDATE, INTERVAL, etc.).
8) SQL must be ONE line, no newlines.

If the user asks for forecasting/prediction/future values:
- Set intent = "forecast".
- STILL only return a SQL statement that fetches the HISTORICAL, TIME-SERIES data needed for forecasting (e.g., monthly sales).
- Do NOT include forecast logic in SQL.

Use these relationships when relevant:
{rel_text or "(none provided)"}

Schema (tables and columns):
{schema}

schema_dict (for validation hints):
{json.dumps({k:list(v) for k,v in schema_dict.items()}, indent=2)[:4000]}

Date ranges (optional):
{json.dumps(date_ranges or {}, indent=2)[:2000]}

Now output ONLY the JSON plan for this user query. Do NOT include explanations or markdown.
"""

    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0
        )

        content = chat.choices[0].message.content
        content = _strip_code_fences(content)

        # try parse JSON
        plan = json.loads(content)

        # basic shape check
        if not isinstance(plan, dict):
            return None
        if "intent" not in plan or "chart_type" not in plan or "sql" not in plan:
            return None

        # normalize whitespace and force single line
        plan["sql"] = re.sub(r'\s+', ' ', plan["sql"]).strip()
        # safety guard
        if re.search(r'\b(UPDATE|DELETE|DROP|INSERT|ALTER)\b', plan["sql"], re.IGNORECASE):
            logging.warning(f"[BLOCKED SQL by LLM plan] {plan['sql']}")
            return None

        return plan

    except Exception as e:
        logging.error(f"[LLM PLAN ERROR] {e}")
        return None

