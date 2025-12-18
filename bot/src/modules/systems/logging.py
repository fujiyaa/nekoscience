


import asyncio
from datetime import datetime

from bot.src.config import ALL_UPDATES_LOG, DELETED_MESSAGES_LOG


log_queue = asyncio.Queue()
logger_task = None
logger_lock = asyncio.Lock()

async def logger_worker():
    while True:
        update = await log_queue.get()
        if update is None:
            break

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{now}] Update in chat {update.effective_chat.id}, "
                f"topic {getattr(update.effective_message, 'message_thread_id', None)}: {update}\n")

        with open(ALL_UPDATES_LOG, "a", encoding="utf-8") as f:
            f.write(line)

        log_queue.task_done()

async def ensure_logger_started():
    global logger_task
    async with logger_lock:
        if logger_task is None:
            logger_task = asyncio.create_task(logger_worker())

async def log_all_update(update):
    await ensure_logger_started()
    await log_queue.put(update)

async def stop_logger():
    await log_queue.put(None)
    await logger_task

def log_deleted_message(user, message_text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DELETED_MESSAGES_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Удалено сообщение от пользователя {user}:\n{message_text}\n\n")
