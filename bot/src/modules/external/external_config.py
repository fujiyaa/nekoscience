


import asyncio
from bot.src.config import MAX_CONCURRENT_REQUESTS

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  
