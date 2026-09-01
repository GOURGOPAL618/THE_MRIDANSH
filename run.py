"""
THE MRIDANSH - Server Launcher
Bypasses the '6_dashboard' invalid package name issue by injecting the
api directory directly into sys.path, allowing uvicorn to import main:app
without requiring a valid top-level Python package name.
"""

import os
import sys

# Inject the api directory so 'main' is importable directly
API_DIR = os.path.join(os.path.dirname(__file__), "6_dashboard", "api")
sys.path.insert(0, API_DIR)

# Inject 2_data_pipeline so 'preprocessing' package is importable
DATA_PIPELINE_DIR = os.path.join(os.path.dirname(__file__), "2_data_pipeline")
sys.path.insert(0, DATA_PIPELINE_DIR)

import uvicorn

if __name__ == "__main__":
    print(">> Starting THE MRIDANSH FastAPI Server on http://127.0.0.1:8000 ...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[API_DIR],
    )
