from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import json, sys, pathlib, os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils import localapi
from utils.botstats import(
    PERIODS,
    calculate_stats_and_graph,
)

templates = Jinja2Templates(directory="templates")
router = APIRouter()

file_u = "file_dashboard_last_update"
file_s = "file_dashboard_bot_stats"

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent 
LOG_FILE = BASE_DIR / "storage" / "bot_data" / "all_updates.log"
UPDATE_COOLDOWN = timedelta(minutes=30)

async def _fetch(key: str):
    path = os.getenv(key)
    if not path:
        return {}
    resp = await localapi.read_file_neko(key)
    data = resp.get("current", {})
    return data if isinstance(data, dict) else {}
    
async def set_last_update(ts: datetime, data):
    await localapi.insert_to_file_neko(file_u, {
        "last_update": ts.isoformat()
    })

    await localapi.insert_to_file_neko(file_s, data)

async def get_last_update():
    data = await _fetch(file_u)
    try:
        ts = data.get("last_update")
        if not ts:
            return None
        return datetime.fromisoformat(ts)
    except Exception:
        return None

async def get_stats():
    return await _fetch(file_s)

async def update_stats_if_needed():
    now = datetime.utcnow()
    last = await get_last_update()

    if last and now - last < UPDATE_COOLDOWN:
        return False 

    with LOG_FILE.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    for period_name, delta in PERIODS.items():
        data[period_name] = calculate_stats_and_graph(lines, delta, period_name)
    
    await set_last_update(now, data)
    return True


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    await update_stats_if_needed()

    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api/data")
async def get_data(period: str = "month"):
    data = await get_stats()
    
    if period not in data:
        raise HTTPException(status_code=404, detail=f"Period '{period}' not found")

    stats = data[period]


    return {
        "all_stats": {
            "total_requests": stats["total_requests"],
            "users": stats["users"],
            "chats": stats["chats"],
            "commands": stats["commands"],
            "user_map": stats.get("user_map", {}),
            "command_map": stats.get("command_map", {}),
            "chart": stats["chart"] 
        }
    }
