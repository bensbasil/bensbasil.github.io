import sys
import os
sys.path.append(os.getcwd())
try:
    from app.main import app
    print("App imported successfully")
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
