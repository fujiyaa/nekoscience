


import asyncio

from .....systems.logging import log_all_update
from .profile import profile



async def start_profile(update, context):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, 'profile'))

async def start_mods(update, context):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, 'mods'))

async def start_mappers(update, context):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, 'mappers'))

async def start_anime(update, context):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, 'anime'))

async def start_average(update, context):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, 'average'))
