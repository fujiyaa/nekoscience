from config import *

async def _post_neko(endpoint: str, payload: dict) -> dict:
    REQUEST_TIMEOUT = 5
    URL = f"{LOCAL_API_URL}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": LOCAL_API_KEY
    }

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(URL, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise RuntimeError(f"neko API returned HTTP {resp.status}")

        except asyncio.TimeoutError:
            raise RuntimeError(f"neko API request timed out after {REQUEST_TIMEOUT}s")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"neko API request failed: {e}")


async def get_score_pp_neko_api(payload: dict) -> dict:
    return await _post_neko("score-pp", payload)


async def get_pp_parts_neko_api(payload: dict) -> dict:
    return await _post_neko("pp-parts", payload)

async def get_map_stats_neko_api(payload: dict) -> dict:
    return await _post_neko("map-stats", payload)

