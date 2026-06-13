from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from .type import format_stats 

from .....actions.members import check_all
from .....external.osu_api import (
    get_user_profile_batch,
    get_top_100_scores_batch,
)
from .....systems.auth import (
    check_osu_verified,
    get_all_osu_verified_telegram_ids,
)

CHAT_CACHE_TTL = 20 * 60
USER_CACHE_TTL = 20 * 60

_chat_cache = {}
_user_cache = {}



async def get_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _chat_cache, _user_cache

    now = datetime.now()
    chat_id = update.effective_chat.id

    # очистка устаревшего formatted-кэша
    expired_users = [
        username
        for username, data in _user_cache.items()
        if (now - data["timestamp"]).total_seconds() > USER_CACHE_TTL
    ]

    for username in expired_users:
        _user_cache.pop(username, None)

    # чат кэш (список участников)
    cached_chat = _chat_cache.get(chat_id)

    if cached_chat and (now - cached_chat["timestamp"]).total_seconds() <= CHAT_CACHE_TTL:
        present = cached_chat["members"]
    else:
        all_ids = await get_all_osu_verified_telegram_ids()
        results = await check_all(context.bot, chat_id, all_ids)

        present = [tg_id for tg_id, status in results if status]

        _chat_cache[chat_id] = {
            "members": present,
            "timestamp": now,
        }

    result = []

    # определяем кого нужно пересчитать
    usernames_to_build = []

    usernames = []

    for tg_id in present:
        username = await check_osu_verified(tg_id)
        if not username:
            continue

        usernames.append(username)

        # кэш хранит ТОЛЬКО formatted
        cached = _user_cache.get(username)
        if not cached or "formatted" not in cached:
            usernames_to_build.append(username)

    # если есть кого обновить — грузим данные
    if usernames_to_build:
        profiles = await get_user_profile_batch(usernames_to_build)

        username_to_profile = {
            p["username"]: p
            for p in profiles
            if p and p.get("username")
        }

        user_ids = [
            username_to_profile[u]["id"]
            for u in usernames_to_build
            if u in username_to_profile
        ]

        top100_map = await get_top_100_scores_batch(user_ids) if user_ids else {}

        # сбор formatted + запись в кэш
        for username in usernames_to_build:
            profile = username_to_profile.get(username)
            if not profile:
                continue

            user_id = profile.get("id")

            raw_item = {
                "username": username,
                "profile": profile,
                "top_100": top100_map.get(user_id, []),
            }

            formatted = await format_stats(raw_item)

            _user_cache[username] = {
                "formatted": formatted,
                "timestamp": now,
            }

    # финальный сбор результата
    for username in usernames:
        cached = _user_cache.get(username)
        if cached and "formatted" in cached:
            result.append(cached["formatted"])

    return result

async def get_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _chat_cache

    now = datetime.now()
    chat_id = update.effective_chat.id

    cached = _chat_cache.get(chat_id)

    if cached and (now - cached["timestamp"]).total_seconds() <= CHAT_CACHE_TTL:
        return cached["members"]

    all_ids = await get_all_osu_verified_telegram_ids()

    results = await check_all(context.bot, chat_id, all_ids)

    present = [
        tg_id
        for tg_id, status in results
        if status
    ]

    _chat_cache[chat_id] = {
        "members": present,
        "timestamp": now
    }

    return present

async def get_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _chat_cache

    now = datetime.now()
    chat_id = update.effective_chat.id

    cached = _chat_cache.get(chat_id)

    if cached and (now - cached["timestamp"]).total_seconds() <= CHAT_CACHE_TTL:
        return cached["members"]

    all_ids = await get_all_osu_verified_telegram_ids()

    results = await check_all(context.bot, chat_id, all_ids)

    present = [
        tg_id
        for tg_id, status in results
        if status
    ]

    _chat_cache[chat_id] = {
        "members": present,
        "timestamp": now
    }

    return present