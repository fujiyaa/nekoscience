


from telegram import Update
from datetime import datetime, timedelta

EXPIRATION = timedelta(days=7)
MAX_NORMAL = 100
MAX_REPLY = 1000

cached_maps = {}       # (chat_id, thread_id) -> data
replies_cache = {}     # (chat_id, thread_id, bot_msg_id) -> data



def _thread_key(update, msg_id=None):
    try:
        chat_id = update.effective_chat.id
        msg = update.effective_message
        thread_id = getattr(msg, "message_thread_id", None)
    except Exception:
        chat_id = update["chat_id"]
        thread_id = update["message_thread_id"]

    if msg_id is not None:
        return (chat_id, thread_id, msg_id)

    return (chat_id, thread_id)


def set_cached_map(update: Update, map_id: int, user_id: int, bot_msg_id: int):
    now = datetime.now()
    tkey = _thread_key(update)

    cached_maps[tkey] = {
        "map_id": map_id,
        "user_id": user_id,
        "ts": now,
        "origin_msg_id": bot_msg_id,
    }

    replies_cache[(tkey[0], tkey[1], bot_msg_id)] = {
        "map_id": map_id,
        "user_id": user_id,
        "ts": now,
        "origin_msg_id": bot_msg_id,
    }

    _cleanup()


def get_cached_map(update: Update):
    now = datetime.now()
    msg = update.effective_message

    # 1. normal reply
    if msg.reply_to_message:
        bot_msg_id = msg.reply_to_message.message_id
        chat_id = update.effective_chat.id

        for (c_id, thread_id, m_id), data in replies_cache.items():
            if c_id == chat_id and m_id == bot_msg_id:
                if now - data["ts"] <= EXPIRATION:
                    return data
                break

    # 2. external reply
    ext = getattr(msg, "external_reply", None)
    if ext:
        bot_msg_id = ext.message_id
        chat_id = update.effective_chat.id

        for (c_id, thread_id, m_id), data in replies_cache.items():
            if c_id == chat_id and m_id == bot_msg_id:
                if now - data["ts"] <= EXPIRATION:
                    return data
                break
        
    # 3. normal cache
    tkey = _thread_key(update)
    data = cached_maps.get(tkey)
    if data and now - data["ts"] <= EXPIRATION:
        return data

    return None


def _cleanup():
    now = datetime.now()

    for tkey in list(cached_maps):
        if now - cached_maps[tkey]["ts"] > EXPIRATION:
            del cached_maps[tkey]

    for rkey, data in list(replies_cache.items()):
        if now - data["ts"] > EXPIRATION:
            del replies_cache[rkey]

    if len(cached_maps) > MAX_NORMAL:
        by_time = sorted(cached_maps.items(), key=lambda x: x[1]["ts"])
        to_delete = by_time[: len(cached_maps) - MAX_NORMAL]
        for tkey, _ in to_delete:
            del cached_maps[tkey]

    if len(replies_cache) > MAX_REPLY:
        by_time = sorted(replies_cache.items(), key=lambda x: x[1]["ts"])
        to_delete = by_time[: len(replies_cache) - MAX_REPLY]
        for rkey, _ in to_delete:
            del replies_cache[rkey]
