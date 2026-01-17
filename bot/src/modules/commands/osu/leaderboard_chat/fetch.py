


from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from ....external.osu_api import get_user_profile_batch
from ....systems.auth import check_osu_verified, get_all_osu_verified_telegram_ids
from ....actions.members import check_all

CACHE_TTL = 20 * 60
_cached_profiles: dict = {}



async def get_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _cached_profiles

    chat_id = update.effective_chat.id
    now = datetime.now()

    expired = [
        tg_id for tg_id, data in _cached_profiles.items()
        if not data.get("timestamp") or (now - data["timestamp"]).total_seconds() > CACHE_TTL
    ]
    for tg_id in expired:
        _cached_profiles.pop(tg_id, None)

    all_ids = await get_all_osu_verified_telegram_ids()
    results = await check_all(context.bot, chat_id, all_ids)

    present = [tg_id for tg_id, status in results if status]

    usernames_to_fetch = []
    tg_id_to_username = {}

    for tg_id in present:
        if tg_id in _cached_profiles:
            _cached_profiles[tg_id].setdefault("chats", set()).add(chat_id)
        else:
            username = await check_osu_verified(tg_id)
            usernames_to_fetch.append(username)
            tg_id_to_username[username] = tg_id

    if usernames_to_fetch:
        fetched = await get_user_profile_batch(usernames_to_fetch)
        for profile in fetched:
            username = profile.get("username")
            tg_id = tg_id_to_username.get(username)
            if tg_id:
                _cached_profiles[tg_id] = {
                    "profile": profile,
                    "timestamp": now,
                    "chats": {chat_id}
                }

    profiles = [
        data["profile"]
        for data in _cached_profiles.values()
        if chat_id in data.get("chats", set())
    ]

    return profiles