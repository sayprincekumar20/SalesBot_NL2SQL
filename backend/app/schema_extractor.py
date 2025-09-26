import sqlite3
import logging
from app.db import DB_PATH

logger = logging.getLogger(__name__)

def extract_schema():
    try:
        abs_db_path = DB_PATH.resolve()
        logger.info(f"Attempting to connect to database at: {abs_db_path}")

        if not abs_db_path.exists():
            raise FileNotFoundError(f"Database file not found: {abs_db_path}")

        conn = sqlite3.connect(str(abs_db_path))
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
        logger.info(f"Successfully extracted schema for {len(tables)} tables")
        return "\n".join(schema), schema_dict, relationships

    except Exception as e:
        logger.error(f"Error extracting schema: {e}")
        raise

def get_table_date_ranges():
    """Heuristic: detect min/max dates for columns containing 'date'."""
    try:
        abs_db_path = DB_PATH.resolve()
        conn = sqlite3.connect(str(abs_db_path))
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
                    pass

            if table_ranges:
                result[table] = table_ranges

        conn.close()
        return result

    except Exception as e:
        logger.error(f"Error getting date ranges: {e}")
        return {}
