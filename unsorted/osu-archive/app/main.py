import os
import sqlite3
import hashlib
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html"
DB_PATH = DATA_DIR / "meta.db"

os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# init sqlite if needed
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
      id TEXT PRIMARY KEY,
      forum_id INTEGER,
      original_url TEXT,
      title TEXT,
      saved_at TEXT,
      client_id TEXT,
      file_name TEXT,
      status TEXT DEFAULT 'active' -- active | deleted
    )
    """)
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="Osu Archive MVP")

class UploadPayload(BaseModel):
    url: str
    title: Optional[str] = ""
    timestamp: Optional[str] = None
    html: str
    client_id: Optional[str] = None
    forum_id: Optional[int] = None

@app.post("/api/upload")
async def upload(payload: UploadPayload):
    if not payload.url or not payload.html:
        raise HTTPException(status_code=400, detail="missing url or html")

    ts = payload.timestamp or datetime.utcnow().isoformat()
    h = hashlib.sha1((payload.url + "|" + ts).encode("utf-8")).hexdigest()
    filename = f"{h}.html"
    filepath = HTML_DIR / filename

    # save html
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(payload.html)

    # determine forum id if not provided (simple heuristic: /forums/<id>/)
    forum_id = payload.forum_id
    if forum_id is None:
        try:
            # crude parse
            # looks for '/forums/{id}/' in url
            parts = payload.url.split("/")
            if "forums" in parts:
                idx = parts.index("forums")
                forum_id = int(parts[idx + 1])
        except Exception:
            forum_id = None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO snapshots (id, forum_id, original_url, title, saved_at, client_id, file_name, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (h, forum_id, payload.url, payload.title, ts, payload.client_id, filename, "active")
    )
    conn.commit()
    conn.close()

    return {"ok": True, "id": h}

@app.get("/api/forum/{forum_id}/archived")
async def forum_archived(forum_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, original_url, saved_at, status FROM snapshots WHERE forum_id = ?", (forum_id,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1] or r[2],
            "original_url": r[2],
            "saved_at": r[3],
            "status": r[4]
        })
    return JSONResponse(result)

@app.get("/archive/{snap_id}", response_class=HTMLResponse)
async def get_archive(snap_id: str):
    # serve the saved html file
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT file_name FROM snapshots WHERE id = ?", (snap_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="snapshot not found")
    filename = row[0]
    filepath = HTML_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="file missing")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content)

# helper endpoint for tests: mark a snapshot as deleted
@app.post("/api/mark_deleted/{snap_id}")
async def mark_deleted(snap_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE snapshots SET status = 'deleted' WHERE id = ?", (snap_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "id": snap_id}

# simple index
@app.get("/")
async def index():
    return {"service": "osu-archive-mvp"}
