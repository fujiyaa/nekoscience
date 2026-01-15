


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

    now = datetime.now()

    expired_keys = []
    for tg_id, data in _cached_profiles.items():
        timestamp = data.get("timestamp")
        if not timestamp or (now - timestamp).total_seconds() > CACHE_TTL:
            expired_keys.append(tg_id)
    for key in expired_keys:
        _cached_profiles.pop(key)

    all_ids = await get_all_osu_verified_telegram_ids()    
    results = await check_all(context.bot, update.effective_chat.id, all_ids)

    usernames_to_fetch = []
    tg_id_to_username = {}
    for tg_id, status in results:
        if status:
            username = await check_osu_verified(tg_id)
            if tg_id not in _cached_profiles:
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
                    "timestamp": now
                }

    profiles = [data["profile"] for data in _cached_profiles.values()]

    return profiles
