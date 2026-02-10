import sys
import os

# Add the current directory to the sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

try:
    from app.main import app
except ImportError as e:
    print(f"FAILED TO IMPORT APP: {e}")
    # This will help debugging on Vercel logs
    raise e
