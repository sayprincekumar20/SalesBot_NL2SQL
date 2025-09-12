import sqlite3
from app.db import DB_PATH

def extract_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = []
    schema_dict = {}
    relationships = []

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for (table,) in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        columns = cursor.fetchall()
        col_defs = ", ".join([col[1] for col in columns])
        schema.append(f"{table}({col_defs})")
        schema_dict[table] = {col[1] for col in columns}

        cursor.execute(f'PRAGMA foreign_key_list("{table}");')
        fks = cursor.fetchall()
        for fk in fks:
            relationships.append({
                "from_table": table,
                "from_col": fk[3],
                "to_table": fk[2],
                "to_col": fk[4],
            })

    conn.close()
    return "\n".join(schema), schema_dict, relationships


def get_table_date_ranges():
    """
    Heuristic: any column name containing 'date' (case-insensitive) is treated as date-like.
    Returns {table: {date_col: {"min": "...", "max": "..."}}}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    result = {}
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        cols = [row[1] for row in cursor.fetchall()]
        date_cols = [c for c in cols if "date" in c.lower()]
        if not date_cols:
            continue

        table_ranges = {}
        for dc in date_cols:
            try:
                cursor.execute(f'SELECT MIN("{dc}"), MAX("{dc}") FROM "{table}"')
                mn, mx = cursor.fetchone()
                if mn is not None and mx is not None:
                    table_ranges[dc] = {"min": str(mn), "max": str(mx)}
            except Exception:
                # ignore any weird types
                pass

        if table_ranges:
            result[table] = table_ranges

    conn.close()
    return result
