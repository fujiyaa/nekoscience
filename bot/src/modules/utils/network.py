


import aiohttp, asyncio

async def post_with_timeout(session: aiohttp.ClientSession, url: str, headers: dict, json_body: dict, timeout: int = 10):
    async with session.post(url, headers=headers, json=json_body, timeout=timeout) as response:
        response.raise_for_status()
        return await response.json()
    
async def fetch_with_timeout(session, url, headers=None, timeout_sec=10):
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        async with session.get(url, headers=headers, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request to {url} failed: {e}")
        return None
    
async def try_request(coro, retries=3, delay=1, *args, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            return await coro(*args, **kwargs)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == retries:
                print(f"Последняя попытка не удалась: {e}")
                raise
            print(f"Сетевая ошибка: {e}, попытка {attempt}/{retries}, повтор через {delay}s...")
            await asyncio.sleep(delay)