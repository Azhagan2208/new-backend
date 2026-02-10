import sys
import os

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Debug: Print path to see if app folder is visible
print(f"Current Path: {sys.path}")
print(f"Directory Contents: {os.listdir(BASE_DIR)}")

try:
    from app.main import app
except Exception as e:
    print(f"Import Error Details: {e}")
    raise e
