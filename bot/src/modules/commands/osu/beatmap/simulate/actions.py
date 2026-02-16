


import asyncio

from .....actions.messages import delete_user_message, delete_message_after_delay



async def clear_s_chat(update, context, msg_chat_id, msg_message_id, delay_1, delay_2):
    asyncio.create_task(delete_user_message(update, context, delay=delay_1))
    asyncio.create_task(delete_message_after_delay(context, msg_chat_id, msg_message_id, delay_2))
