"""UrjaSetu AI — Vercel serverless function: GET /api/health"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402

from urjasetu import __version__  # noqa: E402

app = FastAPI()


@app.api_route("/{path:path}", methods=["GET"])
def health(path: str):
    return {"status": "ok", "version": __version__, "runtime": "vercel-serverless"}
