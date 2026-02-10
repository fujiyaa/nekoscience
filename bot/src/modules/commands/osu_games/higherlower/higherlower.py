


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message
from ....external.osu_api import get_osu_token
from ....wrappers.score import send_score
from ....actions.context import set_message_context
from .processing_v1 import create_score_compare_image
from ....systems import scores_state_db as db
from ....systems.json_files import load_score_file
import temp

from config import COOLDOWN_DEV_COMMANDS     # why
from config import USER_SETTINGS_FILE
from ....systems.translations import SCORE_CAPTION as T


# не асинхронная потому что вызывается только из асинхронной обертки start_osu_link_handler
async def higherlower(update: Update, context: ContextTypes.DEFAULT_TYPE, requested_by_user = True):
    user_id = str(update.effective_user.id)

    if requested_by_user:
        can_run = await check_user_cooldown(
            command_name="higherlower",
            user_id=user_id,
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_DEV_COMMANDS} секунд"
        )
        if not can_run:
            return
    try:
        if context.args:
            limit = int(context.args[0])
            if limit < 2: raise
        else:
            limit = 2
    except:
        limit = 2

    try:
        token = await get_osu_token()

        # cached_entry =  await get_score_by_id(score_id, token)

        # if not cached_entry:
        #     await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
        #     return

        random_scores = db.find_random_scores(
            version = 3022026,
            mode = 'osu',
            ranked = False, # пока не существует
            failed = False,
            ignore_ids = None,
            sort_by = "pp",
            max_diff = 50,
            limit = limit,
        )
        
        cached_entries = []
        for _, cached_entry in enumerate(random_scores):

            cached_entries.append(load_score_file(cached_entry.get('id')))     
                                  
                    
        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(user_id), {}) 
        l = user_settings.get("lang", "ru")

        
        img_path = await create_score_compare_image(
            cached_entries, 
            language=l,
            hide_values='pp'
        )

        captions = '[тестовая версия]\n'
        for cached_entry in cached_entries:

            osu_api_data = cached_entry.get('osu_api_data', {})
            score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
            map_id = cached_entry.get('map', {}).get('beatmap_id')
            map_url = f"https://osu.ppy.sh/b/{map_id}"
            username = cached_entry.get('user', {}).get('username')
            profile_url = f"https://osu.ppy.sh/u/{username}"

            captions += (
                f"<b><a href='{profile_url}'>{T.get('Profile')[l]}</a></b>  •   "
                f"<b><a href='{score_url}'>{T.get('Score')[l]}</a></b>   •   "          
                f"<b><a href='{map_url}'>{T.get('Beatmap')[l]}</a></b>   •   "
                f"id<code>{map_id}</code>"
                f"\n"
                )            

        try:     
            if img_path:
                bot_msg = await update.message.reply_photo(
                    photo=open(img_path, "rb"),
                    caption=captions,
                    parse_mode="HTML"    
                )
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

    
