


import os
import io
import temp
import traceback

from telegram import Update, InputMediaPhoto, LinkPreviewOptions
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....actions.messages import reset_remove_timer, safe_query_answer
from ....systems.json_files import load_score_file
from ....wrappers.score import process_score_and_image

from config import RS_BUTTONS_TIMEOUT, USER_SETTINGS_FILE, user_sessions



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)   
    
    print(query.data)
    data = query.data.split("_")  # rs_prev_msgid / rs_next_msgid / disabled
    if data[1] == "disabled":
        await safe_query_answer(query)
        return

    action = data[1]
    message_id = int(data[2])

    session = user_sessions.get(message_id)
    if not session:
        await safe_query_answer(query, text="⚠️ Кнопки устарели", show_alert=False)
        return

    if str(update.effective_user.id) != session["user_id"]:
        await safe_query_answer(query, text="⛔ Не твои кнопки", show_alert=True)
        return

    new_index = session["index"]
    if action == "next" and new_index < len(session["scores"]) - 1:
        new_index += 1
    elif action == "prev" and new_index > 0:
        new_index -= 1

    score_id = str(session["scores"][new_index]["osu_api_data"]["id"])
    entry = load_score_file(score_id)

    if not entry:
        await safe_query_answer(query)
        return
    
    if not entry['state']['enriched']:
        await safe_query_answer(query, text="🐟 Загрузка...", show_alert=True)
        return

    await safe_query_answer(query)
    rs_bg_render = False # for now ...
    img_path, caption = await process_score_and_image(entry, image_todo_flag=rs_bg_render)

    total = len(session["scores"])
    buttons = [
        InlineKeyboardButton("⬅️", callback_data=f"rs_prev_{message_id}" if new_index > 0 else "rs_disabled"),
        InlineKeyboardButton(f"{new_index+1}/{total}", callback_data="rs_disabled"),
        InlineKeyboardButton("➡️", callback_data=f"rs_next_{message_id}" if new_index < total - 1 else "rs_disabled")
    ]
    keyboard = InlineKeyboardMarkup([buttons])

    try:
        if img_path and os.path.isfile(img_path) and os.path.getsize(img_path) > 0:
            with open(img_path, "rb") as f:
                bio = io.BytesIO(f.read())
            media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
            await query.edit_message_media(media=media, reply_markup=keyboard)
        else:
            link_preview = LinkPreviewOptions(
                url=entry['map']['card2x_url'],
                is_disabled=False,
                prefer_small_media=False,
                prefer_large_media=True,
                show_above_text=True
            )
            await query.edit_message_text(
                text=caption,
                parse_mode='HTML',
                link_preview_options=link_preview,
                reply_markup=keyboard
            )

        session["index"] = new_index

        reset_remove_timer(
            context.bot,
            query.message.chat.id,
            query.message.message_id,
            RS_BUTTONS_TIMEOUT,
            cleanup=lambda: user_sessions.pop(query.message.message_id, None)
        )

    except Exception:
        traceback.print_exc()
