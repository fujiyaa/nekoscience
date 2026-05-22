


from contextlib import asynccontextmanager

from .locks import GLOBAL_LOCK



@asynccontextmanager
async def transaction():
    async with GLOBAL_LOCK:
        yield
