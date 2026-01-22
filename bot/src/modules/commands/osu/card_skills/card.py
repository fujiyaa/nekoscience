


import io
import os
import aiohttp
import asyncio
import temp
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from models.score import Score 
from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....utils.osu_conversions import is_legacy_score
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_osu_token, get_user_profile 
from ....external.osu_api import get_top_100_scores
from ....external.osu_http import fetch_txt_beatmaps
from ....external.local_skills import get_skills_by_scores
from .processing_v1 import make_card

from config import COOLDOWN_CARD_COMMAND, USER_SETTINGS_FILE, CARDS_DIR
from config import AVATARS_DIR, message_authors



async def start_skills(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(skills(update, context, user_request))

#нужна массивная чистка
async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="skills",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.effective_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )
    elif query:
        if query.message.text or query.message.caption:
            temp_message = await query.message.edit_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )
        else:
            temp_message = await query.message.reply_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/skills Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    message_authors[temp_message.message_id] = update.effective_user.id
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            
            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(user_id), {}) 
            user_data["lang"] = user_settings.get("lang", "ru") 
        
            try:
                user_id = user_data["id"]  # изменить на percent("NM") < 10: другом количестве скоров!!!
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id, limit=30, plain=True), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)  

            scores = []
            unique_maps = set()
            
            maps_ids = []
            for score in best_scores:
                map_id = score["beatmap"]["id"]
                maps_ids.append(map_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            if failed:
                print("err loading maps (skills):", failed)

            for score in best_scores:
                map_id = score["beatmap"]["id"]
                path = results.get(map_id, None)
                unique_maps.add((map_id, tuple(score.get("mods", []))))
                stats = score["statistics"]
                count_300 = stats.get("count_300", 0)
                count_100 = stats.get("count_100", 0)
                count_50 = stats.get("count_50", 0)
                count_miss = stats.get("count_miss", 0)    
                if is_legacy_score(score): lazer = False 
                else: lazer = True    
                
                score["lazer"] = lazer       
                scores.append(Score(
                    map_id=map_id,
                    count_300=count_300,
                    count_100=count_100,
                    count_50=count_50,
                    count_miss=count_miss,
                    path=path,
                    mods=score.get("mods", []), 
                    acc=score.get("accuracy", 1.0),            
                    max_combo=score.get("max_combo", 0),
                    lazer=lazer
                ))

            #neko api 
            skills = await get_skills_by_scores(best_scores)
            if not skills: 
                print('Error: no skills')
                return
            

            username = user_data["username"]
            stats = user_data["statistics"]
            pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
            global_rank = f"{stats.get('global_rank'):,}" if stats.get("global_rank") else "N/A"
            country_rank = f"{stats.get('country_rank'):,}" if stats.get("country_rank") else "N/A"            
            country_code = user_data["country_code"]

            medals = len(user_data['user_achievements'])
            
            level_data = stats.get('level', {})
            current = level_data.get('current', 0)
            progress = level_data.get('progress', 0)

            level = float(f"{current}.{progress}")

            avatar_url = user_data["avatar_url"]
            user_id = user_data["id"]
            
            now = datetime.now()
            avatar_file = None
            for f in os.listdir(AVATARS_DIR):
                if f.startswith(f"{user_id}_") and f.endswith(".png"):
                    path = os.path.join(AVATARS_DIR, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    if now - mtime < timedelta(hours=1):
                        avatar_file = path
                        break
            
            if avatar_file:
                extra_img = Image.open(avatar_file).convert("RGBA")
                avatar_path = avatar_file
                print("using cached avatar")
            else:
                avatar_path = os.path.join(AVATARS_DIR, "default.png")
                extra_img = None
                for attempt_avatar in range(1, MAX_ATTEMPTS + 1):
                    try:
                        timeout = aiohttp.ClientTimeout(total=3)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(avatar_url) as resp:
                                if resp.status == 200:
                                    def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:                                            
                                        big_size = (img.size[0]*2, img.size[1]*2)
                                        mask = Image.new("L", big_size, 0)
                                        draw_mask = ImageDraw.Draw(mask)
                                        draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                        
                                        mask = mask.resize(img.size, Image.LANCZOS)
                                        
                                        img.putalpha(mask)
                                        return img
                                    extra_img_data = await resp.read()
                                    extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                                    extra_img.thumbnail((512, 512))
                                    extra_img = add_rounded_corners(extra_img, radius=12)
                                    avatar_filename = f"{user_id}_{now.hour}{now.minute}.png"
                                    avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
                                    extra_img.save(avatar_path, format="PNG")
                                    break
                    except Exception as e:
                        print(f"Ошибка при скачивании аватарки: {e}")

            img_path = make_card(
                scores,
                username,
                country_code, 
                avatar_path,
                skills,
                global_rank,
                country_rank,
                level,
                medals,
                mode="Standard",########################################
                output=f"{CARDS_DIR}/{user_data['id']}.png",
            )

                    
            with open(img_path, "rb") as f:
                try:
                    await message.reply_photo(InputFile(f))
                except:
                    await message.reply_photo(InputFile(f))
            
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            except:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)

            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Ошибка при удалении файла {img_path}: {e}")
            return

        except Exception as e:
            print(f"Ошибка при skills (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
