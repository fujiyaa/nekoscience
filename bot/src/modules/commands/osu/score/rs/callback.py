


import os
import io
import temp
import traceback
import asyncio

from telegram import Update, InputMediaPhoto, LinkPreviewOptions
from telegram.ext import ContextTypes

from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....actions.messages import reset_remove_timer, safe_query_answer, safe_edit_query, try_send
from .....systems.json_files import load_score_file
from .....wrappers.score import process_score_and_image
from .....wrappers.score_image_v2 import get_score_caption
from .....actions.context import set_message_context
from .....image_processing.workflows.score_adaptive.processing_v1 import create_score_compare_image
from .....systems.images import delayed_remove
from .buttons import get_keyboard

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
    user_id = str(update.effective_user.id)

    if not session:
        await safe_query_answer(query, text="⚠️ Кнопки устарели", show_alert=False)
        return

    if user_id != session["user_id"]:
        await safe_query_answer(query, text="⛔ Не твои кнопки", show_alert=True)
        return
    
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(user_id), {})
    l = user_settings.get("lang", "ru")

    new_index = session["index"]
    total = len(session["scores"])

    session = user_sessions.get(message_id)
    if not session:
        return

    if action == "switchExt":     
        session["keyboardExt"] = not session["keyboardExt"]

        reply_markup = await get_keyboard(
            new_index,
            total,
            message_id,
            extended=session["keyboardExt"]
        )

        await try_send(
            update.effective_message.edit_reply_markup,
            reply_markup=reply_markup
        )

        reset_remove_timer(
            context.bot,
            update.effective_chat.id,
            message_id,
            RS_BUTTONS_TIMEOUT,
            cleanup=lambda: user_sessions.pop(message_id, None)
        )
        return
    
    elif action == "scoreExt":
        reply_markup = await get_keyboard(
            new_index,
            total,
            message_id,
            extended=session["keyboardExt"],
            loading_image_flag=True 
        )
        await try_send(
            update.effective_message.edit_reply_markup,
            reply_markup=reply_markup
        )
        
        score_id = str(session["scores"][new_index]["osu_api_data"]["id"])
        cached_entry = load_score_file(score_id)
        
        scores = []
        scores.append(cached_entry)
        img_path = await create_score_compare_image(scores, language=l)
        
        caption = await get_score_caption(cached_entry, l)

        if img_path:
            with open(img_path, "rb") as f:
                bio = io.BytesIO(f.read())

            media = InputMediaPhoto(
                media=bio, 
                caption=caption, 
                parse_mode="HTML"
            )           

            bot_msg = await query.edit_message_media(
                media=media, 
                reply_markup=None
            )
        
            asyncio.create_task(delayed_remove(img_path))

        return

    elif action == "next":
        new_index += 1
    elif action == "nextExt":
        new_index += 10
    elif action == "endExt":
        new_index = total - 1
    elif action == "prev":
        new_index -= 1
    elif action == "prevExt":
        new_index -= 10
    elif action == "startExt":
        new_index = 0

    new_index = max(0, min(new_index, total - 1))

    score_id = str(session["scores"][new_index]["osu_api_data"]["id"])
    entry = load_score_file(score_id)

    if not entry:
        await safe_query_answer(query)
        return
    
    await safe_query_answer(query)
    rs_bg_render = False # for now ...
    img_path, caption = await process_score_and_image(entry, image_todo_flag=rs_bg_render)
    
    if message_id in user_sessions:
        keyboardExt = user_sessions[message_id]["keyboardExt"]

    reply_markup = await get_keyboard(new_index, len(session["scores"]), message_id, keyboardExt)

    try:
        if img_path and os.path.isfile(img_path) and os.path.getsize(img_path) > 0:
            with open(img_path, "rb") as f:
                bio = io.BytesIO(f.read())
            media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
            bot_msg = await query.edit_message_media(media=media, reply_markup=reply_markup)
        else:
            link_preview = LinkPreviewOptions(
                url=entry['map']['card2x_url'],
                is_disabled=False,
                prefer_small_media=False,
                prefer_large_media=True,
                show_above_text=True
            )
            bot_msg = await query.edit_message_text(
                text=caption,
                parse_mode='HTML',
                link_preview_options=link_preview,
                reply_markup=reply_markup
            )

        session["index"] = new_index

        map_id=entry.get('map').get('beatmap_id')

        if bot_msg:
            set_message_context(
                        bot_msg, 
                        reply=False, 
                        map_id=map_id,
                        map_title=await get_beatmap_title_from_file(map_id),
                        mapper_username=await get_beatmap_creator_from_file(map_id), 
                        origin_call_user_id=update.effective_user.id,
                    )
            
        reset_remove_timer(
            context.bot,
            query.message.chat.id,
            query.message.message_id,
            RS_BUTTONS_TIMEOUT,
            cleanup=lambda: user_sessions.pop(query.message.message_id, None)
        )

    except Exception:
        traceback.print_exc()
