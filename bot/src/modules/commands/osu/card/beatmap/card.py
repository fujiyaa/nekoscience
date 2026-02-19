


import os
import asyncio

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from .....systems.logging import log_all_update
from .....systems.cooldowns import check_user_cooldown
from .....actions.messages import delete_user_message, delete_message_after_delay, safe_send_message
from .....external.osu_http import fetch_txt_beatmaps
from .....external.osu_api import get_osu_token, get_beatmap
from .....actions.context import set_message_context, get_message_context
from .context.buttons import get_context_keyboard
from .buttons import get_keyboard
from .processing_v1 import create_beatmap_image
from .utils import delayed_remove
import temp

from config import USER_SETTINGS_FILE
from config import OSU_MAP_REGEX, COOLDOWN_CARD_COMMAND



async def  start_beatmap_card(update, context, user_request=True):
    if user_request: await log_all_update(update)
    asyncio.create_task(beatmap_card(update, context, user_request))

async def beatmap_card(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):    
    try:
        map_id = None

        message_text = update.message.text.strip()
        match = OSU_MAP_REGEX.search(message_text)
        message = update.message

        if user_request:
            if not match:
                message_context = get_message_context(update, reply=False)          
                message_context_reply = get_message_context(update, reply=True)      
                if message_context:
                    m1 = m2 = None
                    m1 = message_context["metadata"].get("map_id")
                    if message_context_reply:
                        m2 = message_context_reply["metadata"].get("map_id")
            
                    if (m1 is not None) or (m2 is not None):
                        message_context_reply = get_message_context(update, reply=True)
                                    
                        await safe_send_message(
                            update, 
                            text=f"<code>Выбери карту...\n(или отправь ссылку)</code>", 
                            reply_markup=get_context_keyboard(
                                message_context,
                                message_context_reply,
                                update.effective_user.id,
                                update.effective_message.id,
                            ),
                            parse_mode="HTML"
                        )
                        return

                msg = await update.message.reply_text(
                    text = (
                        f"✖️ Для карточки нужна ссылка на карту\n\n"
                        f"<i>Ищешь поиск карт? <code>/help inline</code></i>\n"
                    ),                    
                    parse_mode = "HTML"
                )
                asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
                asyncio.create_task(delete_user_message(update, context, delay=10))
                return
        
        if match is None: 
            return
        
        if map_id is None:
            beatmap_id = match.group(1) if match.group(1) else match.group(2)
        else:
            beatmap_id = map_id
    
        if user_request: warn_text = f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        else: warn_text = None
        can_run = await check_user_cooldown(
            command_name="render_score",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=warn_text
        )
        if not can_run:
            return
    
    except Exception as e:
        print(e)
        return
    
    

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                if update.message:
                    temp_message = await update.message.reply_text(
                        "`Загрузка...`",
                        parse_mode="Markdown"
                    )
                break
            except Exception as e: print(e)
  
    for _ in range(max_attempts):
        try:             
            maps_ids = []
            maps_ids.append(beatmap_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(beatmap_id, token)

            user_id = str(update.effective_user.id)

            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(user_id), {}) 
            _new_card = user_settings.get("new_card", True)
            map_data["lang"] = user_settings.get("lang", "ru")

            img_path = await create_beatmap_image(map_data, beatmap_id)             

            with open(img_path, "rb") as f:
                try:
                    reply_markup = await get_keyboard(str(beatmap_id))
                    bot_msg = await message.reply_photo(
                        InputFile(f), reply_markup = reply_markup
                    )
                except:
                    bot_msg = await message.reply_photo(
                        InputFile(f),
                    )
                if user_request:
                    try:                        
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                    except:
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            
            asyncio.create_task(delayed_remove(img_path))

            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False, 
                    map_id=beatmap_id,
                    map_title=map_data['beatmapset']['title'], 
                    mapper_username=map_data['owners'][0]['username'],
                    origin_call_user_id=update.effective_user.id,
                )

            return
        except Exception as e: print(e)   
