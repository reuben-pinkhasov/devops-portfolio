from fastapi import FastAPI
from fastapi.responses import FileResponse
from .main import run_investigation

from pathlib import Path


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="DevOps AI Troubleshooting Agent",
    description=(
        "AI-powered Kubernetes and AWS SRE "
        "troubleshooting API."
    ),
    version="1.0.0",
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"

INDEX_FILE = STATIC_DIR / "index.html"


# =========================================================
# WEB UI
# =========================================================

@app.get("/")
def home():
    return FileResponse(INDEX_FILE)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "DevOps AI Troubleshooting Agent",
    }

@app.get("/api")
def api_info():
    return {
        "service": "DevOps AI Troubleshooting Agent",
        "version": "1.0.0",
        "endpoints": {
            "web_ui": "/",
            "health": "/health",
            "investigate": "/investigate",
            "swagger": "/docs",
        },
    }
# =========================================================
# INVESTIGATION
# =========================================================

@app.post("/investigate")
def investigate():
    """
    Run the complete Kubernetes/AWS investigation
    and return the structured SRE report.
    """

    report = run_investigation()

    return report