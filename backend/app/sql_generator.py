# from app.llm import generate_sql
# from app.db import run_sql
# from app.schema_extractor import extract_schema
# import logging
# import re
# from collections import defaultdict, deque
# from app.summarizer import summarize_data

# # Load schema, schema_dict, relationships
# schema, schema_dict, relationships = extract_schema()


# def generate_alias(table_name: str, used_aliases: set) -> str:
#     """Generate short unique alias for table"""
#     alias = "".join([w[0].lower() for w in table_name.split()])[:3]
#     orig_alias = alias
#     counter = 1
#     while alias in used_aliases:
#         alias = f"{orig_alias}{counter}"
#         counter += 1
#     used_aliases.add(alias)
#     return alias


# def validate_sql(query: str) -> bool:
#     """Check if all columns exist in the correct table alias"""
#     column_matches = re.findall(r'(\w+)\.(\w+)', query)
#     for alias, col in column_matches:
#         table_found = False
#         for table, cols in schema_dict.items():
#             if generate_alias(table, set()) == alias:
#                 if col not in cols:
#                     logging.warning(f"[INVALID COLUMN] {alias}.{col} does not exist in {table}")
#                     return False
#                 table_found = True
#                 break
#         if not table_found:
#             logging.warning(f"[UNKNOWN ALIAS] {alias} not found for column {col}")
#             return False
#     return True


# def find_join_path(tables: list[str], target_columns: list[str] = None) -> list[dict]:
#     """BFS to find shortest join path connecting tables/columns"""
#     graph = defaultdict(list)
#     for rel in relationships:
#         graph[rel['from_table']].append((rel['to_table'], rel['from_col'], rel['to_col']))
#         graph[rel['to_table']].append((rel['from_table'], rel['to_col'], rel['from_col']))

#     all_tables = set(tables)
#     if target_columns:
#         for col in target_columns:
#             for table, cols in schema_dict.items():
#                 if col in cols:
#                     all_tables.add(table)

#     path_edges = []
#     visited = set()
#     queue = deque([tables[0]])
#     visited.add(tables[0])

#     while queue:
#         current = queue.popleft()
#         for neighbor, from_col, to_col in graph[current]:
#             if neighbor not in visited and neighbor in all_tables:
#                 path_edges.append({
#                     'from_table': current,
#                     'to_table': neighbor,
#                     'from_col': from_col,
#                     'to_col': to_col
#                 })
#                 queue.append(neighbor)
#                 visited.add(neighbor)
#             if visited >= all_tables:
#                 return path_edges
#     return path_edges


# def fix_table_names(query: str, schema_dict: dict) -> str:
#     """
#     Normalize table names:
#       - Always quote tables (with spaces).
#       - Use exactly one alias per table.
#       - Reuse alias if already present.
#       - Prevent double/triple quotes.
#     """
#     used_aliases = set()
#     table_alias_map = {}

#     # Normalize Orders → "Orders" but only if not already quoted
#     normalization_map = {table.replace(" ", "").lower(): table for table in schema_dict}
#     for norm, exact in normalization_map.items():
#         query = re.sub(
#             rf'\b{norm}\b',
#             f'"{exact}"',
#             query,
#             flags=re.IGNORECASE
#         )

#     for table in schema_dict:
#         # Ensure table is quoted exactly once
#         query = re.sub(
#             rf'("{re.escape(table)}"+|\b{re.escape(table)}\b)',
#             f'"{table}"',
#             query
#         )

#         # Detect existing alias ("Customers" c)
#         alias_pattern = rf'"{re.escape(table)}"\s+(\w+)'
#         match = re.search(alias_pattern, query)

#         if match:
#             alias = match.group(1)  # reuse alias
#         else:
#             alias = generate_alias(table, used_aliases)
#             query = re.sub(rf'"{re.escape(table)}"', f'"{table}" {alias}', query, count=1)

#         table_alias_map[table] = alias
#         used_aliases.add(alias)

#         # Replace col refs: "Orders".OrderID → o.OrderID
#         query = re.sub(rf'"{re.escape(table)}"\.(\w+)', f'{alias}.\\1', query)

#     # Final cleanup: remove any accidental double quotes
#     query = re.sub(r'"+', '"', query)
#     query = re.sub(r'\s+', ' ', query).strip()
#     return query


# def fix_invalid_joins(query: str) -> str:
#     """Fix joins to include tables containing required columns"""
#     tables_in_query = set(re.findall(r'FROM\s+(\S+)|JOIN\s+(\S+)', query, re.IGNORECASE))
#     tables_in_query = set([t[0] or t[1] for t in tables_in_query])

#     columns_in_query = re.findall(r'\b\w+\.(\w+)\b', query)

#     join_path = find_join_path(list(tables_in_query), columns_in_query)
#     if not join_path:
#         return query

#     # Build FROM + JOIN clauses
#     used_aliases = set()
#     aliases = {t: generate_alias(t, used_aliases) for edge in join_path for t in [edge['from_table'], edge['to_table']]}
#     first_table = join_path[0]['from_table']
#     clauses = [f'"{first_table}" {aliases[first_table]}']
#     for edge in join_path:
#         clauses.append(
#             f'JOIN "{edge["to_table"]}" {aliases[edge["to_table"]]} '
#             f'ON {aliases[edge["from_table"]]}.{edge["from_col"]} = {aliases[edge["to_table"]]}.{edge["to_col"]}'
#         )

#     query = re.sub(r'FROM\s+.+?(?=WHERE|GROUP BY|ORDER BY|$)',
#                    "FROM " + " ".join(clauses), query, flags=re.IGNORECASE | re.DOTALL)

#     # Update column references
#     for col in columns_in_query:
#         for table, cols in schema_dict.items():
#             if col in cols:
#                 alias = aliases.get(table, generate_alias(table, used_aliases))
#                 query = re.sub(rf'(\b)\w+\.{col}(\b)', f'{alias}.{col}', query)

#     return query


# def handle_sql(prompt: str, max_retries: int = 3):
#     """Main SQL generation and execution pipeline"""
#     query = generate_sql(prompt, schema, relationships)
#     if query is None:
#         return {"intent": "historical", 
#                 "query": None, 
#                 "data": None,
#                 "message": "Blocked unsafe SQL."
#                 }

#     query = fix_table_names(query, schema_dict)
#     retries = 0

#     while retries < max_retries and not validate_sql(query):
#         logging.info(f"[RETRY {retries+1}] Invalid SQL detected. Query: {query}")
#         query = fix_invalid_joins(query)

#         # llm retry if still invalid
#         query = generate_sql(
#             f"Retry and fix this SQL using valid tables/columns/relationships:\n{schema}\n\nQuery:\n{query}\nPrompt:\n{prompt}",
#             schema,
#             relationships
#         )
#         if query is None:
#             return {"intent": "historical",
#                      "query": None, 
#                      "data": None,
#                      "message": "Blocked unsafe SQL after retry."
#                      }

#         query = fix_table_names(query, schema_dict)
#         retries += 1

#     data = run_sql(query)
#     if isinstance(data, dict) and "error" in data:
#         return {"intent": "historical",
#                 "query": query,
#                 "data": None, 
#                 "message": f"SQL Error: {data['error']}"}

#     return {"intent": "historical",
#             "query": query,
#             "data": data,
#             "message": "Query executed successfully."}



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
