


import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.auth import check_osu_verified, get_osu_id
from .....external.localapi import read_file_neko, insert_to_file_neko, remove_from_file_neko
from .....systems.json_files import load_score_file
from .....systems.images import delayed_remove
from ..processing_v1 import create_score_compare_image
from ..buttons import get_keyboard
from ..utils import calculate_max_diff
from ..json_schema import construct_user, construct_active
# from .filter import filter_other_topics
from .....systems import scores_state_db as db
import temp

from config import COOLDOWN_HLGAME_COMMANDS, USER_SETTINGS_FILE
from .....systems.translations import SCORE_CAPTION as T

MAX_ATTEMPTS = 1

d_file = "file_osugames_higherlower"



async def send_score_compare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    cached_entries: list,
    tg_name: str,
    current_score: int,
    current_health: int,
    scores_quantity: int,
    best_score: int,
    user_id: str
):
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(user_id), {})
    lang = user_settings.get("lang", "ru")

    img_path = await create_score_compare_image(
        cached_entries,
        language=lang,
        hide_values='pp'
    )

    health_text = "🤍" * current_health
    
    captions = (
        f"✴️ @{tg_name}, где <b>больше pp</b>?\n"
    )

    captions += (
        f"Текущая игра: <b>{current_score}</b> угадано, рекорд: <b>{best_score}</b>\n"
        f"<b>HP</b>: {health_text}\n"        
    )
    
    reply_markup = get_keyboard(f"next_{scores_quantity}")

    if img_path:
        if update.callback_query.message.message_id:
            media = InputMediaPhoto(
                media=open(img_path, "rb"),
                caption=captions,
                parse_mode="HTML"
            )

            await context.bot.edit_message_media(
                chat_id=update.effective_chat.id,
                message_id=update.callback_query.message.message_id,
                media=media,
                reply_markup=reply_markup
            )
        else:
            await update.effective_message.reply_photo(
                photo=open(img_path, "rb"),
                caption=captions,
                reply_markup=reply_markup,
                parse_mode="HTML"    
            )
            
        asyncio.create_task(delayed_remove(img_path))
    else:
        raise()

async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE, scores_quantity:int = 2):
    user_id = str(update.effective_user.id)
    
    can_run = await check_user_cooldown(
        command_name="higherlower_game_next",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_HLGAME_COMMANDS,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_HLGAME_COMMANDS} секунд"
    )
    if not can_run or update.effective_user.username is None:
        return

    tg_id = update.effective_user.id
    tg_name = update.effective_user.username

    osu_name = await check_osu_verified(user_id)
    if not osu_name:
        await safe_send_message(update, "⚠ Не сохранен ник, это делается командой /name", parse_mode="Markdown")
        return

    osu_id = await get_osu_id(user_id)
    if not osu_id:
        return
    osu_id = str(osu_id)

    response = await read_file_neko(d_file)
    data = response.get("current", {})

    if osu_id not in data:
        data[osu_id] = construct_user(osu_id, osu_name, tg_id, tg_name)
        await insert_to_file_neko(d_file, data)

    user = data[osu_id]
    v1 = user["v1"]
    active = v1.get("active")
    completed = v1.get("completed") or {}
    skipped = v1.get("skipped") or {}
    osu = user.get("osu")
    osu_name, osu_id = osu.get("username"), osu.get("id")
    
    points = v1.get("points", {})
    current_score = points.get("current_score", 0)
    average_score = points.get("average_score", 0)
    best_score = points.get("best_score", 0)
    current_health = points.get("current_health", 0)

    if active:
        cached_entries = [load_score_file(id) for id in active.get("scores_ids", [])]
        if not cached_entries:
            await safe_send_message(update, "❌ Ошибка, попробуй еще раз", parse_mode="HTML")
            return
        await send_score_compare(update, context, cached_entries, tg_name, current_score, current_health, scores_quantity, best_score, user_id)
    
    else:
        if current_health == 0:
            current_health = 3
            current_score = 0

        MAX_SEARCH_ATTEMPTS = 5
        for _ in range(MAX_SEARCH_ATTEMPTS):
            random_scores = db.find_random_scores(
                version=3022026,
                mode='osu',
                ranked=False,
                failed=False,
                ignore_ids=None,
                sort_by="pp",
                max_diff=calculate_max_diff(current_score),
                limit=scores_quantity,
            )
            cached_entries = [load_score_file(entry.get('id')) for entry in random_scores]
            if len(cached_entries) == scores_quantity:
                break
        else:
            await safe_send_message(update, "❌ Ошибка, попробуй еще раз", parse_mode="HTML")
            return

        await send_score_compare(update, context, cached_entries, tg_name, current_score, current_health, scores_quantity, best_score, user_id)

        scores_active = construct_active(cached_entries, 'pp', 0, 0)
        await remove_from_file_neko(d_file, [osu_id])
        v1_new = {
            "points": {
                "current_score": current_score,
                "average_score": int(points.get("average_score", 0)),
                "best_score": int(points.get("best_score", 0)),
                "current_health": current_health
            },
            "active": scores_active,
            "skipped": skipped,
            "completed": completed
        }
        data[osu_id] = construct_user(osu_id, osu_name, tg_id, tg_name, v1=v1_new)
        await insert_to_file_neko(d_file, data)
