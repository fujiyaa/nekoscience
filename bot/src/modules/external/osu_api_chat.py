


import os
import asyncio
import json
import aiohttp
import time
import uuid
import traceback

from config import OSU_PROFILE_ACCESS_TOKEN

API_CHAT_BASE = "https://osu.ppy.sh"
TOKEN_FILE = "osu_tokens.json"

refresh_lock = asyncio.Lock()

API_BASE = "https://osu.ppy.sh/api/v2"
MAX_ATTEMPTS = 3
AUTH_MODE = None  # "FULL" | "FALLBACK" | "NONE"

class OsuAuthState:
    def __init__(self):
        self.tokens = {
            "access_token": None,
            "refresh_token": None,
            "expires_at": 0
        }
        self.mode = None
        self.lock = asyncio.Lock()

STATE = OsuAuthState()

async def send_pm(target_id: int, message: str, action: bool = False, timeout_sec: int = 10):

    url = f"{API_BASE}/chat/new"

    for attempt in range(1, MAX_ATTEMPTS + 1):

        token = await get_chat_api_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "target_id": target_id,
            "message": message,
            "is_action": action,
            "uuid": str(uuid.uuid4())
        }

        timeout = aiohttp.ClientTimeout(total=timeout_sec)

        print(f"🔻 send_pm attempt {attempt}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.json()

        except Exception as e:
            print(f"send_pm failed attempt {attempt}: {repr(e)}")
            traceback.print_exc()

            if attempt == MAX_ATTEMPTS:
                return None

            await asyncio.sleep(1)

def save_tokens():
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(STATE.tokens, f, indent=4)


def load_tokens():
    path = os.path.abspath(TOKEN_FILE)

    print("🔻 [TOKENS LOAD]")
    print(f"Path: {path}")

    if not os.path.exists(path):
        print("⚠ File not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        STATE.tokens = json.load(f)

    if STATE.tokens.get("refresh_token"):
        STATE.mode = "FULL"

    print("🔻 [TOKENS LOAD SUCCESS]")


def update_tokens(new_tokens: dict):
    STATE.tokens = new_tokens
    save_tokens()
    print("osu tokens updated")

def needs_refresh():
    if STATE.mode != "FULL":
        return False

    expires_at = STATE.tokens.get("expires_at")

    if not isinstance(expires_at, (int, float)):
        return False

    if expires_at == float("inf"):
        return False

    return time.time() >= expires_at - 300

async def post_json(url: str, headers: dict, payload: dict, timeout_sec: int = 10):
    timeout = aiohttp.ClientTimeout(total=timeout_sec)

    print(f"🔻 API POST: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                resp.raise_for_status()
                return await resp.json()

    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request failed: {e}")
        return None
    
CLIENT_ID = "39582"
CLIENT_SECRET = "gLG8u0YUd8BrxtVN6sLSSWJZxOaxuPki3243ZRVS"

async def refresh_access_token():
    url = "https://osu.ppy.sh/oauth/token"

    payload = {
        "client_id": int(CLIENT_ID),
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": STATE.tokens.get("refresh_token")
    }

    headers = {
        "Accept": "application/json"
    }

    data = await post_json(url, headers, payload)

    if not data:
        print("⚠ refresh returned empty response")
        return None

    if "access_token" not in data:
        print("⚠ invalid refresh response:", data)
        return None

    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", STATE.tokens.get("refresh_token")),
        "expires_at": time.time() + data["expires_in"]
    }

async def refresh_tokens():
    async with STATE.lock:

        if not needs_refresh():
            return

        print("refreshing osu token...")

        new_tokens = await refresh_access_token()

        if not new_tokens:
            print("⚠ refresh failed")
            return

        STATE.tokens = new_tokens
        save_tokens()

async def get_chat_api_token():

    if STATE.mode is None:
        raise Exception("AUTH not initialized yet")

    if STATE.mode == "FALLBACK":
        return STATE.tokens["access_token"]

    if STATE.mode != "FULL":
        raise Exception(f"No auth available: {STATE.mode}")

    if needs_refresh():
        await refresh_tokens()

    return STATE.tokens["access_token"]

async def auto_refresh_task():

    while True:
        try:
            if STATE.mode == "FULL" and STATE.tokens.get("refresh_token"):
                if needs_refresh():
                    await refresh_tokens()

            await asyncio.sleep(60)

        except Exception as e:
            print("auto refresh error:", e)
            await asyncio.sleep(30)

async def init_osu_auth():
    load_tokens()

    if STATE.tokens.get("refresh_token"):
        STATE.mode = "FULL"
        await refresh_tokens()
        asyncio.create_task(auto_refresh_task())
        print("FULL MODE")
        return

    if OSU_PROFILE_ACCESS_TOKEN:
        STATE.mode = "FALLBACK"
        STATE.tokens["access_token"] = OSU_PROFILE_ACCESS_TOKEN
        STATE.tokens["expires_at"] = float("inf")
        print("FALLBACK MODE")
        return

    STATE.mode = "NONE"
    print("No auth")