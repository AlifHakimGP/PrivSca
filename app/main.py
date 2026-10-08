"""
main.py — API + static file serving, same "one process" pattern as the
push-dashboard project, but with a plain HTML/CSS/JS frontend instead of
React this time — there's no build step to reason about at all here.
"""

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .scanner import scan_url

app = FastAPI(title="Privacy Scanner")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class ScanRequest(BaseModel):
    url: str


@app.post("/api/scan")
async def api_scan(body: ScanRequest):
    target = body.url.strip()
    if not target:
        raise HTTPException(status_code=400, detail="Please provide a URL.")
    if not target.startswith(("http://", "https://")):
        target = "https://" + target  # let people type "example.com" too

    try:
        return await scan_url(target)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"That site responded with an error: HTTP {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Couldn't reach that URL: {e}")


# Mounted LAST and at "/" — FastAPI checks explicitly-declared routes
# (like /api/scan above) before falling through to a mount, so this
# correctly catches everything else and serves static/index.html for "/".
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
