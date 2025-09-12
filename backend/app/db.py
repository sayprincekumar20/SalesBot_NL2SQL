import sqlite3
import logging
import base64

DB_PATH = "data/northwind.db"

def run_sql(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        data = []
        for row in rows:
            row_dict = {}
            for col, val in zip(columns, row):
                if isinstance(val, bytes):
                    logging.warning(f"Skipping binary column: {col}")
                    continue
                else:
                    row_dict[col] = val
            data.append(row_dict)

        return data

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()

