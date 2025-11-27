from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import json
import aiohttp
import os, random, string
from pathlib import Path
from datetime import datetime, timedelta

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

templates = Jinja2Templates(directory="templates")

DEV = os.getenv("DEV_FLAG", "0") == "1"

if not DEV:
    OSU_CLIENT_ID = os.getenv("OSU_CLIENT_ID_BOT_AUTH")
    OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET_BOT_AUTH")
    OSU_REDIRECT_URI = os.getenv("OSU_REDIRECT_URI_BOT_AUTH")
else:
    OSU_CLIENT_ID = os.getenv("DEV_OSU_CLIENT_ID_BOT_AUTH")
    OSU_CLIENT_SECRET = os.getenv("DEV_OSU_CLIENT_SECRET_BOT_AUTH")
    OSU_REDIRECT_URI = os.getenv("DEV_OSU_REDIRECT_URI_BOT_AUTH")

file_id = "file_osu_pending" 

err_url = (
        "https://osu.ppy.sh/oauth/authorize"
        f"?client_id={OSU_CLIENT_ID}"
        f"&redirect_uri={OSU_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )

router = APIRouter()


from utils.localapi import read_file_neko, insert_to_file_neko, remove_from_file_neko

from datetime import datetime, timedelta

async def update_codes(file_id: str, username: str, osu_id: int):    
    response = await read_file_neko(file_id)
    current = response.get("current", {})

    if not isinstance(current, dict):
        current = {}

    now = datetime.utcnow()
    keys_to_remove = []

    for k, v in current.items():
        if not isinstance(v, dict):
            continue
        created_at_str = v.get("created_at")
        if not created_at_str:
            keys_to_remove.append(k)
            continue
        created_at = datetime.fromisoformat(created_at_str)
        if now - created_at > timedelta(days=7) or v.get("username") == username:
            keys_to_remove.append(k)

    if keys_to_remove:
        await remove_from_file_neko(file_id, keys_to_remove)

    new_code = generate_code()
    while new_code in current:
        new_code = generate_code()

    await insert_to_file_neko(file_id, {
        new_code: {
            "osu_id": osu_id,
            "username": username,
            "created_at": now.isoformat()
        }
    })

    return new_code



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

    if os.getenv(file_id):
        new_code = await update_codes(file_id, username, id)
    else:
        new_code = "error"

    return templates.TemplateResponse("darkness_auth_code.html", {
        "request": request,
        "username": username,
        "code": new_code
    })