# test_db_fix.py
import sys
import os
sys.path.append('..')

from app.db import DB_PATH, init_database

print("=== TESTING DB PATH ===")
print(f"DB_PATH: {DB_PATH}")
print(f"Exists: {DB_PATH.exists()}")

if DB_PATH.exists():
    print("✅ Database path is correct!")
    db_ok = init_database()
    print(f"Database accessible: {db_ok}")
    
    # Test schema extraction
    try:
        from app.schema_extractor import extract_schema
        schema, schema_dict, relationships = extract_schema()
        print(f"✅ Schema extraction successful!")
        print(f"Tables found: {len(schema_dict)}")
        print(f"Sample tables: {list(schema_dict.keys())[:5]}")
    except Exception as e:
        print(f"❌ Schema extraction failed: {e}")
else:
    print("❌ Database path still incorrect!")