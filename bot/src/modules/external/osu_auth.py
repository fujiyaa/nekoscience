


import aiohttp, asyncio, time

from bot.src.config import OSU_CLIENT_ID, OSU_CLIENT_SECRET

_cached_token = None
_token_expiry = 0
async def get_osu_token(timeout_sec: int = 10):
    global _cached_token, _token_expiry
    now = time.time()

    if _cached_token and now < _token_expiry:
        return _cached_token

    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        print('🔻 API request (token)')
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://osu.ppy.sh/oauth/token",
                json={
                    "client_id": OSU_CLIENT_ID,
                    "client_secret": OSU_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                    "scope": "public"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _cached_token = data.get("access_token")
                    expires_in = data.get("expires_in", 60) 
                    _token_expiry = now + expires_in - 5  
                    return _cached_token
                else:
                    print(f"Token request failed with status {resp.status}")
                    return None
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Token request error: {e}")
        return None