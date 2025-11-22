from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import json
import aiohttp
import os, random, string
from pathlib import Path
from datetime import datetime, timedelta

templates = Jinja2Templates(directory="templates")

if not os.getenv("DEV_FLAG", "0"):
    OSU_CLIENT_ID = os.getenv("OSU_CLIENT_ID_BOT_AUTH")
    OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET_BOT_AUTH")
    OSU_REDIRECT_URI = os.getenv("OSU_REDIRECT_URI_BOT_AUTH")
else:
    OSU_CLIENT_ID = os.getenv("DEV_OSU_CLIENT_ID_BOT_AUTH")
    OSU_CLIENT_SECRET = os.getenv("DEV_OSU_CLIENT_SECRET_BOT_AUTH")
    OSU_REDIRECT_URI = os.getenv("DEV_OSU_REDIRECT_URI_BOT_AUTH")

BASE_DIR = Path(__file__).resolve().parents[3]  # nekoscience/
# USER_FILE = BASE_DIR / "bot" / "src" / "stats" / "data" / "users.json"
VERIFY_PENDING_FILE = BASE_DIR / "web" / "src" / "auth" / "pending.json"

err_url = (
        "https://osu.ppy.sh/oauth/authorize"
        f"?client_id={OSU_CLIENT_ID}"
        f"&redirect_uri={OSU_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )

router = APIRouter()


def load_codes():
    if not VERIFY_PENDING_FILE.exists():
        VERIFY_PENDING_FILE.write_text("{}", encoding="utf-8")
    try:
        return json.loads(VERIFY_PENDING_FILE.read_text("utf-8"))
    except:
        return {}


def save_codes(data):
    VERIFY_PENDING_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )


def generate_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))


@router.get("/darkness/auth")
async def root_redirect():    
    return RedirectResponse(err_url)


@router.get("/darkness/oauth/callback")
async def oauth_callback(request: Request, code: str = None):
    if not code:
        oauth_url = (
            "https://osu.ppy.sh/oauth/authorize"
            f"?client_id={OSU_CLIENT_ID}"
            f"&redirect_uri={OSU_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify"
        )
        return RedirectResponse(oauth_url)

    async with aiohttp.ClientSession() as session:
        async with session.post("https://osu.ppy.sh/oauth/token", json={
            "client_id": OSU_CLIENT_ID,
            "client_secret": OSU_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OSU_REDIRECT_URI
        }) as resp:
            token_data = await resp.json()

    access_token = token_data.get("access_token")
    if not access_token:        
        return RedirectResponse(err_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://osu.ppy.sh/api/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ) as resp:
            user_data = await resp.json()

    username = user_data.get("username")
    id = user_data.get("id")

    codes = load_codes()

    now = datetime.utcnow()
    codes = {k: v for k, v in codes.items() 
             if now - datetime.fromisoformat(v["created_at"]) < timedelta(days=7)}

    codes = {k: v for k, v in codes.items() if v["username"] != username}

    new_code = generate_code()
    while new_code in codes:
        new_code = generate_code()

    codes[new_code] = {
        "osu_id": id,
        "username": username,
        "created_at": now.isoformat()
    }

    save_codes(codes)

    return templates.TemplateResponse("darkness_auth_code.html", {
        "request": request,
        "username": username,
        "code": new_code
    })