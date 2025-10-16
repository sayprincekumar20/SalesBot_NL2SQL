# debug_paths.py
from pathlib import Path

# Directories
APP_DIR = Path(__file__).resolve().parent        # backend/app
BACKEND_DIR = APP_DIR.parent                     # backend
PROJECT_ROOT = BACKEND_DIR.parent                # Should be SalesBot_NL2SQL

print("=== PATH DEBUG ===")
print(f"APP_DIR: {APP_DIR}")
print(f"BACKEND_DIR: {BACKEND_DIR}")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"PROJECT_ROOT.parent: {PROJECT_ROOT.parent}")

# Check what we're getting
expected_path = PROJECT_ROOT.parent / "data" / "northwind.db"
print(f"Expected DB path: {expected_path}")
print(f"Expected exists: {expected_path.exists()}")

# What should it be?
correct_path = PROJECT_ROOT / "data" / "northwind.db"
print(f"Correct DB path: {correct_path}")
print(f"Correct exists: {correct_path.exists()}")