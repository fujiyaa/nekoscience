


import random
import time
import traceback
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
from ..json_schema import construct_user, construct_active
# from .filter import filter_other_topics
from .....systems import scores_state_db as db
import temp

from config import COOLDOWN_HLGAME_COMMANDS, USER_SETTINGS_FILE
from .....systems.translations import SCORE_CAPTION as T

MAX_ATTEMPTS = 1

d_file = "file_osugames_higherlower"



async def finish_game(update: Update, context: ContextTypes.DEFAULT_TYPE, score_selected:int):
    # if not await filter_other_topics(update, context): 
    #     return
    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="higherlower_game_finish",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_HLGAME_COMMANDS,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_HLGAME_COMMANDS} секунд"        
    )    
    if not can_run or update.effective_user.username is None:
        return    
    else:    
        tg_id = update.effective_user.id 
        tg_name = update.effective_user.username

    for _ in range(MAX_ATTEMPTS):
        try:                   
            osu_name = await check_osu_verified(user_id)
            if not osu_name:
                return            
            
            osu_id = await get_osu_id(user_id)
            if osu_id: 
                osu_id = str(osu_id) 
            else: 
                return    
            
            response = await read_file_neko(d_file)
            data = response.get("current", {})

            if osu_id not in data:
                return

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
                active_scores_ids = active.get("scores_ids", [])
                cached_entries = []
                for _, id in enumerate(active_scores_ids):

                    cached_entries.append(load_score_file(id))

                if not cached_entries:        
                    await safe_send_message(update, text="❌ Ошибка, попробуй еще раз", parse_mode="HTML")
                    return           

                
                # 1. сначала отправить сообщение

                s = temp.load_json(USER_SETTINGS_FILE, default={})
                user_settings = s.get(str(user_id), {}) 
                l = user_settings.get("lang", "ru")

                
                img_path = await create_score_compare_image(
                    cached_entries, 
                    language=l
                )

                stat = active.get("value_to_guess", "")

                def is_highest(entries, selected_index, stat):
                    values = []
                    for entry in entries:
                        neko = entry.get("neko_api_calc", {})
                        osu_score = entry.get("osu_score", {})

                        if stat == "pp":
                            osu_pp = osu_score.get("pp")

                            if isinstance(osu_pp, (int, float)) and osu_pp > 0:
                                value = osu_pp
                            else:
                                value = neko.get("pp", 0)
                        else:
                            value = neko.get(stat, 0)

                        values.append(value)

                        print(values)

                    selected_value = values[selected_index-1]
                    return selected_value == max(values)
                
                now = time.time()                
                bonus_text = ''

                print(cached_entries[0]['neko_api_calc']['pp'])
                print(cached_entries[1]['neko_api_calc']['pp'])
                print(score_selected, is_highest(cached_entries, score_selected, stat))

                if is_highest(cached_entries, score_selected, stat):  

                    average_score += 1
                    current_score += 1 # score
                    current_health += 1

                    bonus_text = '+1'

                    if best_score < current_score:
                        best_score = current_score

                        if random.random() < 0.10:  # 10%
                            current_health += 1
                            bonus_text = '+2 (бонус за рекорд)'

                    for id in active_scores_ids:
                        completed[str(id)] = now   

                    captions = (
                        f"✅ @{tg_name}, правильно...\n"
                    )
                else:                    
                    average_score -= 1
                    current_health -= 1 # health

                    for id in active_scores_ids:
                        skipped[str(id)] = now  

                    bonus_text = '-1'

                    captions = (
                        f"❌ @{tg_name}, неправильно...\n"
                    )

                health_text = "🤍" * current_health
                    
                captions += (
                    f"Текущая игра: <b>{current_score}</b> угадано, рекорд: <b>{best_score}</b>\n"
                    f"<b>HP</b>: {health_text} <code>{bonus_text}</code>\n\n"        
                )

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

                if current_score < 75:
                    next_scores_quantity = 2
                else:
                    next_scores_quantity = 3                
                                 
                reply_markup = get_keyboard(f"finish_{next_scores_quantity}")

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
                

                # 2. потом редактировать файлы
                                
                keys_to_remove = []
                keys_to_remove.append(osu_id)

                await remove_from_file_neko(d_file, keys_to_remove)

                v1_new = {
                    "points": {
                        "current_score":        current_score,
                        "average_score":        average_score,
                        "best_score":           best_score,
                        "current_health":       current_health
                    },
                    "active":                   None,
                    "skipped":                  skipped,
                    "completed":                completed
                }

                data[osu_id] = construct_user(
                    osu_id, 
                    osu_name, 
                    tg_id,
                    tg_name,
                    v1 = v1_new
                )

                await insert_to_file_neko(d_file, data)           
            
            
            return
        except Exception:
            traceback.print_exc()
