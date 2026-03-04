


import asyncio

from ...systems.logging import log_all_update
from .complex import vote
from .filter import is_allowed_chat



async def start_vote_delete_message(update, context):
    if not is_allowed_chat(update):
        return
     
    await log_all_update(update)
    asyncio.create_task(vote(update, context, 'delete_message'))

async def start_message_info(update, context):
    await log_all_update(update)
    asyncio.create_task(vote(update, context, 'message_info'))
