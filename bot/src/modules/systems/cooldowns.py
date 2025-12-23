


import os, aiofiles, json, asyncio
from datetime import datetime, timedelta, timezone
from modules.actions.messages import delete_message_after_delay

from config import COOLDOWN_FILE

async def read_cooldowns():
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    async with aiofiles.open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        try:
            data = await f.read()
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
async def write_cooldowns(data):
    async with aiofiles.open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))
async def check_user_cooldown(command_name: str, user_id: str, cooldown_seconds: int, 
                              update=None, context=None, warn_text=None):
    now = datetime.now(timezone.utc).isoformat()
    cooldown = timedelta(seconds=cooldown_seconds)

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})

    last_used_str = user_cooldowns.get(user_id)
    if last_used_str:
        last_used = datetime.fromisoformat(last_used_str)
        if datetime.now(timezone.utc) - last_used < cooldown:
            if not warn_text is None:
                if update and context:
                    try:
                        await update.message.delete()
                    except Exception:
                        pass
                
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=warn_text,
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 3))
            return False

    user_cooldowns[user_id] = now
    data[command_name] = user_cooldowns
    await write_cooldowns(data)
    return True
async def is_on_cooldown(command_name: str, cooldown_seconds: int) -> bool:
    bot_id = str(727)
    cooldown = timedelta(seconds=cooldown_seconds)

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})
    
    last_used_str = user_cooldowns.get(bot_id)
    if last_used_str:
        last_used = datetime.fromisoformat(last_used_str)
        if datetime.now(timezone.utc) - last_used < cooldown:
            return True
    return False

async def update_cooldown(command_name: str):
    bot_id = str(727)
    now = datetime.now(timezone.utc).isoformat()

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})
    
    user_cooldowns[bot_id] = now
    data[command_name] = user_cooldowns
    await write_cooldowns(data)