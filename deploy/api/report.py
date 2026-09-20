"""UrjaSetu AI — Vercel serverless function: GET /api/report
Baseline vs UrjaSetu AI headline numbers, computed in the cloud from the twin."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402

from urjasetu.report import build_report  # noqa: E402

app = FastAPI()


@app.api_route("/{path:path}", methods=["GET"])
def report(path: str):
    return build_report()
