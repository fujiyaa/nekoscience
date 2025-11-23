import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", None)
LOCAL_API_URL = os.getenv("LOCAL_API_URL", None)

REQUEST_TIMEOUT = 5

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
