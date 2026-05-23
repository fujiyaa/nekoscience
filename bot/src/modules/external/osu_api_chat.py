


import asyncio
import json
import aiohttp
import time
import uuid
import traceback

from config import OSU_PROFILE_ACCESS_TOKEN


TOKENS = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": 0
}

API_CHAT_BASE = "https://osu.ppy.sh"
TOKEN_FILE = "osu_tokens.json"

refresh_lock = asyncio.Lock()

API_BASE = "https://osu.ppy.sh/api/v2"
MAX_ATTEMPTS = 3
AUTH_MODE = None  # "FULL" | "FALLBACK" | "NONE"

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
        json.dump(TOKENS, f, indent=4)

def load_tokens():
    global TOKENS

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            TOKENS = json.load(f)
    except FileNotFoundError:
        pass

def update_tokens(new_tokens: dict):
    global TOKENS
    TOKENS = new_tokens
    save_tokens()
    print("osu tokens updated")

def needs_refresh():
    if AUTH_MODE != "FULL":
        return False

    if not TOKENS.get("expires_at"):
        return False

    return time.time() >= TOKENS["expires_at"] - 300

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
    url = f"https://osu.ppy.sh/oauth/token"

    payload = {
        "client_id": int(CLIENT_ID),
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": TOKENS["refresh_token"]
    }

    headers = {
        "Accept": "application/json"
    }

    data = await post_json(url, headers, payload)

    if not data:
        raise Exception("Failed to refresh token")

    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + data["expires_in"]
    }

async def refresh_tokens():
    async with refresh_lock:

        if not needs_refresh():
            return

        print("refreshing osu token...")

        new_tokens = await refresh_access_token()

        update_tokens(new_tokens)

async def get_chat_api_token():

    if AUTH_MODE == "FALLBACK":
        return TOKENS["access_token"]

    if AUTH_MODE != "FULL":
        raise Exception("No auth available")

    if needs_refresh():
        await refresh_tokens()

    return TOKENS["access_token"]

async def auto_refresh_task():

    while True:
        try:
            if TOKENS.get("refresh_token"):

                if needs_refresh():
                    await refresh_tokens()

            await asyncio.sleep(60)

        except Exception as e:
            print("auto refresh error:")
            print(e)

            await asyncio.sleep(30)

async def init_osu_auth():
    load_tokens()

    global AUTH_MODE

    if TOKENS.get("refresh_token"):
        AUTH_MODE = "FULL"
        await refresh_tokens()
        asyncio.create_task(auto_refresh_task())
        print("osu auth initialized (FULL MODE)")
        return

    if OSU_PROFILE_ACCESS_TOKEN:
        AUTH_MODE = "FALLBACK"
        TOKENS["access_token"] = OSU_PROFILE_ACCESS_TOKEN
        TOKENS["refresh_token"] = None
        TOKENS["expires_at"] = None

        print("osu auth initialized (FALLBACK MODE)")
        return

    AUTH_MODE = "NONE"
    raise Exception("No OAuth and no fallback token")