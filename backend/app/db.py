import sqlite3
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
APP_DIR = Path(__file__).resolve().parent        # backend/app
BACKEND_DIR = APP_DIR.parent                     # backend
PROJECT_ROOT = BACKEND_DIR.parent                # SalesBot_NL2SQL

# --- Handle DB_PATH from environment ---
env_db_path = os.getenv("DB_PATH")

if env_db_path:
    candidate = Path(env_db_path)
    if not candidate.is_absolute():
        # Resolve relative to PROJECT_ROOT
        DB_PATH = (PROJECT_ROOT / candidate).resolve()
    else:
        DB_PATH = candidate.resolve()
else:
    # Default fallback
    DB_PATH = (PROJECT_ROOT / "data" / "northwind.db").resolve()

logger.info(f"DB_PATH from env: {env_db_path}")
logger.info(f"Resolved database path: {DB_PATH}")
logger.info(f"Database file exists: {DB_PATH.exists()}")

def init_database():
    """Verify database exists and is accessible"""
    try:
        abs_db_path = DB_PATH
        logger.info(f"Looking for database at: {abs_db_path}")
        logger.info(f"Current working directory: {os.getcwd()}")

        if not abs_db_path.exists():
            logger.error(f"Database file does not exist: {abs_db_path}")
            return False

        conn = sqlite3.connect(str(abs_db_path))
        # Ensure SQLite returns bytes safely
        conn.text_factory = lambda b: b.decode(errors='ignore')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Found {len(tables)} tables in database")
        if tables:
            logger.info(f"Tables: {[t[0] for t in tables[:5]]}")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error accessing database: {e}")
        return False

def run_sql(query: str):
    """Execute SQL query and return results safely"""
    def safe_str(value):
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return value

    try:
        abs_db_path = DB_PATH
        if not abs_db_path.exists():
            error_msg = f"Database file not found at: {abs_db_path}"
            logger.error(error_msg)
            return {"error": error_msg}

        conn = sqlite3.connect(str(abs_db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.text_factory = lambda b: b.decode(errors='ignore')
        cursor = conn.cursor()
        cursor.execute(query)

        if query.strip().upper().startswith("SELECT"):
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            sanitized_rows = [
                {col: safe_str(val) for col, val in zip(columns, row)}
                for row in rows
            ]
            return sanitized_rows
        else:
            conn.commit()
            return {"message": "Query executed successfully", "rows_affected": cursor.rowcount}

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return {"error": str(e)}

    finally:
        if "conn" in locals():
            conn.close()

# Run a test on import
init_database()
