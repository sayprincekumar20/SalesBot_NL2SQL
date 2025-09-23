# import sqlite3
# import logging
# import base64
# import os

# # Use environment variable with fallback to original path
# DB_PATH = os.getenv('DB_PATH', "data/northwind.db")

# def run_sql(query: str):
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         cursor.execute(query)
#         columns = [col[0] for col in cursor.description]
#         rows = cursor.fetchall()

#         data = []
#         for row in rows:
#             row_dict = {}
#             for col, val in zip(columns, row):
#                 if isinstance(val, bytes):
#                     logging.warning(f"Skipping binary column: {col}")
#                     continue
#                 else:
#                     row_dict[col] = val
#             data.append(row_dict)

#         return data

#     except Exception as e:
#         return {"error": str(e)}

#     finally:
#         if 'conn' in locals():
#             conn.close()

import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variable with fallback to original path
DB_PATH = os.getenv('DB_PATH', "data/northwind.db")

def init_database():
    """Verify database exists and is accessible"""
    try:
        # Get absolute path relative to the application root
        if DB_PATH.startswith('/app/'):
            # Absolute path in Docker
            abs_db_path = DB_PATH
        else:
            # Relative path - resolve from current working directory
            abs_db_path = os.path.abspath(DB_PATH)
        
        logger.info(f"Looking for database at: {abs_db_path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Check if database file exists
        if not os.path.exists(abs_db_path):
            logger.error(f"Database file does not exist: {abs_db_path}")
            # List contents of data directory
            data_dir = os.path.dirname(abs_db_path)
            if os.path.exists(data_dir):
                logger.info(f"Files in data directory: {os.listdir(data_dir)}")
            else:
                logger.error(f"Data directory does not exist: {data_dir}")
            return False
            
        # Test database connection
        conn = sqlite3.connect(abs_db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        logger.info(f"Found {len(tables)} tables in database")
        if tables:
            table_names = [table[0] for table in tables[:10]]  # Show first 10 tables
            logger.info(f"Sample tables: {table_names}")
        
        conn.close()
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Error accessing database: {e}")
        return False

def run_sql(query: str):
    """Execute SQL query and return results"""
    try:
        # Get absolute path
        if DB_PATH.startswith('/app/'):
            abs_db_path = DB_PATH
        else:
            abs_db_path = os.path.abspath(DB_PATH)
        
        # Verify database exists before running query
        if not os.path.exists(abs_db_path):
            error_msg = f"Database file not found at: {abs_db_path}"
            logger.error(error_msg)
            return {"error": error_msg}

        conn = sqlite3.connect(abs_db_path)
        cursor = conn.cursor()

        cursor.execute(query)
        
        # For SELECT queries, return data
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    if isinstance(val, bytes):
                        logger.warning(f"Skipping binary column: {col}")
                        continue
                    else:
                        row_dict[col] = val
                data.append(row_dict)

            return data
        else:
            # For INSERT, UPDATE, DELETE queries
            conn.commit()
            return {"message": "Query executed successfully", "rows_affected": cursor.rowcount}

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return {"error": str(e)}

    finally:
        if 'conn' in locals():
            conn.close()

# Test database connection when module is imported
logger.info("Database module imported")