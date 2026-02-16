


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....systems.cooldowns import check_user_cooldown
from .....actions.messages import safe_send_message
from .....external.osu_api import get_osu_token, get_score_by_id
from .....wrappers.score import send_score
from .....actions.context import set_message_context
from .....systems.images import delayed_remove
from .....image_processing.workflows.score_adaptive.processing_v1 import create_score_compare_image
import temp

from config import COOLDOWN_RS_COMMAND     # why
from config import USER_SETTINGS_FILE
from .....systems.translations import SCORE_CAPTION as T


# не асинхронная потому что вызывается только из асинхронной обертки start_osu_link_handler
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE, requested_by_user = True):
    user_id = str(update.effective_user.id)

    if requested_by_user:
        can_run = await check_user_cooldown(
            command_name="score",
            user_id=user_id,
            cooldown_seconds=COOLDOWN_RS_COMMAND,
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RS_COMMAND} секунд"
        )
        if not can_run:
            return

    if context.args:
        score_id = context.args[0]
    else:
        await safe_send_message(update, "⚠ Не указан ID скора", parse_mode="Markdown")
        return

    try:
        token = await get_osu_token()

        cached_entry =  await get_score_by_id(score_id, token, override = True)

        if not cached_entry:
            await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
            return
        
        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(user_id), {}) 
        render_card = user_settings.get("settings_score_card", False)
        l = user_settings.get("lang", "ru")

        if not render_card:
            bot_msg = await send_score(update, cached_entry, user_id, user_id, user_id, is_recent=False)
        else:
            scores = []
            scores.append(cached_entry)
            img_path = await create_score_compare_image(scores, language=l)
            
            osu_api_data = cached_entry.get('osu_api_data', {})
            score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
            map_id = cached_entry.get('map', {}).get('beatmap_id')
            map_url = f"https://osu.ppy.sh/b/{map_id}"
            username = cached_entry.get('user', {}).get('username')
            profile_url = f"https://osu.ppy.sh/u/{username}"

            caption = (
                f"<b><a href='{profile_url}'>{T.get('Profile')[l]}</a></b>  •   "
                f"<b><a href='{score_url}'>{T.get('Score')[l]}</a></b>   •   "          
                f"<b><a href='{map_url}'>{T.get('Beatmap')[l]}</a></b>   •   "
                f"id<code>{map_id}</code>"
                )            

            try:     
                if img_path:
                    bot_msg = await update.message.reply_photo(
                        photo=open(img_path, "rb"),
                        caption=caption,
                        parse_mode="HTML"    
                    )
                
                    asyncio.create_task(delayed_remove(img_path))

                else:
                    raise() 
            except Exception:
                traceback.print_exc()            

        map_id=cached_entry.get('map').get('beatmap_id')

        if bot_msg:
            set_message_context(
                bot_msg, 
                reply=False, 
                map_id=map_id,
                map_title=await get_beatmap_title_from_file(map_id),
                mapper_username=await get_beatmap_creator_from_file(map_id),  
                origin_call_user_id=update.effective_user.id,
            )
            
    except Exception:
        traceback.print_exc()
        await safe_send_message(update, "❌ Ошибка", parse_mode="Markdown")

    
