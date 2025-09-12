import logging
import json
import re
from typing import Dict, Any, List

from app.llm import generate_plan
from app.db import run_sql
from app.schema_extractor import extract_schema, get_table_date_ranges
from app.summarizer import summarize_data
from app.forecast_service import forecast_arima

# load schema
schema, schema_dict, relationships = extract_schema()
date_ranges = get_table_date_ranges()


def _build_chart_config(chart_type: str, rows: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Produce a generic chart config that your frontend can consume directly.
    Heuristics:
      - if a date/period-like column exists + one numeric metric → line
      - if two columns (label, value) → bar/pie depending on chart_type
      - else → table
    """
    if not rows:
        return None

    # detect label and numeric value
    keys = list(rows[0].keys())

    # find likely label
    label_key = None
    for k in keys:
        if any(s in k.lower() for s in ["date", "month", "year", "period", "category", "region", "product", "name"]):
            label_key = k
            break
    if label_key is None:
        label_key = keys[0]

    # find likely numeric
    def is_num(x):
        return isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())

    num_keys = []
    for k in keys:
        if any(is_num(r.get(k)) for r in rows):
            if k != label_key:
                num_keys.append(k)

    if not num_keys:
        # fallback to table
        return {
            "type": "table",
            "columns": keys,
            "rows": rows
        }

    value_key = None
    for pref in ["sales", "revenue", "amount", "total", "value", "freight"]:
        vk = next((k for k in num_keys if pref in k.lower()), None)
        if vk:
            value_key = vk
            break
    if value_key is None:
        value_key = num_keys[0]

    labels = [str(r.get(label_key)) for r in rows]
    values = []
    for r in rows:
        v = r.get(value_key)
        try:
            values.append(float(v))
        except Exception:
            values.append(0.0)

    # normalize chart_type choice
    cht = chart_type.lower()
    if cht not in {"line", "bar", "pie", "table"}:
        if any(s in label_key.lower() for s in ["date", "month", "year", "period"]):
            cht = "line"
        else:
            cht = "bar"

    if cht == "table":
        return {
            "type": "table",
            "columns": keys,
            "rows": rows
        }

    if cht == "pie":
        # frontends often want label/value pairs
        return {
            "type": "pie",
            "labels": labels,
            "datasets": [
                {"name": value_key, "data": values}
            ]
        }

    if cht == "bar":
        return {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {"name": value_key, "data": values}
            ]
        }

    # default line
    return {
        "type": "line",
        "labels": labels,
        "datasets": [
            {"name": value_key, "data": values}
        ]
    }


def handle_sql(user_prompt: str) -> Dict[str, Any]:
    """
    Single entry point:
      - Ask LLM for plan (intent + chart_type + sql)
      - Execute SQL
      - Build chart JSON
      - Summarize
      - If forecast intent: run ARIMA on returned historical series
    """
    plan = generate_plan(
        user_query=user_prompt,
        schema=schema,
        schema_dict=schema_dict,
        relationships=relationships,
        date_ranges=date_ranges
    )
    if not plan:
        return {
            "intent": "historical",
            "query": None,
            "data": None,
            "chart": None,
            "summary": None,
            "forecast": None,
            "message": "LLM failed to produce a plan."
        }

    intent = (plan.get("intent") or "historical").lower()
    chart_type = plan.get("chart_type", "table")
    sql = plan.get("sql", "")

    # final SQL sanity check
    forbidden = ["UPDATE", "DELETE", "DROP", "INSERT", "ALTER"]
    if any(word in sql.upper() for word in forbidden):
        logging.warning(f"[BLOCKED SQL] {sql}")
        return {
            "intent": intent,
            "query": None,
            "data": None,
            "chart": None,
            "summary": None,
            "forecast": None,
            "message": "Blocked unsafe SQL."
        }

    # Execute SQL
    data = run_sql(sql)
    if isinstance(data, dict) and "error" in data:
        return {
            "intent": intent,
            "query": sql,
            "data": None,
            "chart": None,
            "summary": None,
            "forecast": None,
            "message": f"SQL Error: {data['error']}"
        }

    # Chart
    chart = _build_chart_config(chart_type, data)

    # Summary
    summary = summarize_data(user_prompt, data)

    # Forecast if requested
    forecast = None
    if intent == "forecast":
        forecast = forecast_arima(data, prompt=user_prompt)

        #forecast = forecast_arima(data, horizon=3)

    return {
        "intent": intent,
        "query": sql,
        "data": data,
        "chart": chart,
        "summary": summary,
        "forecast": forecast,
        "message": "Query executed successfully."
    }
