from config import *

REQUEST_TIMEOUT = 5

#rosu & osu
async def _post_neko(endpoint: str, payload: dict) -> dict:
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


#files
async def _post_file(endpoint: str, file_id: str, payload: dict) -> dict:
    url = f"{LOCAL_API_URL}file/{file_id}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": LOCAL_API_KEY
    }
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise RuntimeError(f"File API returned HTTP {resp.status}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"File API request timed out after {REQUEST_TIMEOUT}s")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"File API request failed: {e}")

async def read_file_neko(file_id: str) -> dict:
    url = f"{LOCAL_API_URL}file/{file_id}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": LOCAL_API_KEY
    }
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise RuntimeError(f"File API returned HTTP {resp.status}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"File API request timed out after {REQUEST_TIMEOUT}s")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"File API request failed: {e}")

async def insert_to_file_neko(file_id: str, payload: dict) -> dict:
    return await _post_file("insert", file_id, payload)

async def remove_from_file_neko(file_id: str, keys: list[str]) -> dict:
    payload = {k: None for k in keys}  
    return await _post_file("remove", file_id, payload)



async def get_forum_db_thread_count(dummy: str = "x") -> dict:
    url = f"{LOCAL_API_URL}forum/thread/count/threads/{dummy}"

    headers = {
        "X-API-Key": LOCAL_API_KEY
    }

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise RuntimeError(f"Forum API returned HTTP {resp.status}")

        except asyncio.TimeoutError:
            raise RuntimeError(f"Forum API request timed out after {REQUEST_TIMEOUT}s")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Forum API request failed: {e}")
