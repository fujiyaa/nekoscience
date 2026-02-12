


import os
import asyncio



async def delayed_remove(path, delay=5):
    try:
        await asyncio.sleep(delay)
        os.remove(path)

    except:
        #  уже может быть удален
        pass