


import asyncio
import html

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_http import fetch_txt_beatmaps
from ....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from ....external.localapi import get_score_pp_neko_api
from ....utils.osu_conversions import calculate_weighted_pp
from .buttons import get_keyboard
from .page_text import get_text

from .....config import COOLDOWN_STATS_COMMANDS



async def start_nochoke(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(nochoke(update, context, user_request))

async def nochoke(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="average_stats",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 1  

    user_id = str(update.message.from_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    miss_limit = None
    args = context.args

    if args:
        # %N
        for arg in args:
            if arg.startswith("%") and arg[1:].isdigit():
                miss_limit = int(arg[1:])
                args.remove(arg)
                break
        username = " ".join(args) if args else saved_name
    else:
        username = saved_name

    if not username:
        text = (f"`Нужна помощь?`\n\n"
                f"Сохранить ник: */name*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n"
        )
        await safe_send_message(update, text, parse_mode="Markdown")
        return

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        text=f"`Загрузочка... (20 сек макс.)`\n\n"
                        f"Сохраненный ник: *{saved_name}*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет игрока или статистики...`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)            
            

            if isinstance(best_scores, list) and best_scores:
                live_raw_pp = calculate_weighted_pp(best_scores, bonus_pp=0)
                                
                stats = user_data["statistics"]
                live_pp = f"{stats.get('pp', 0):.2f}"
               
                bonus =  float(live_pp) - float(live_raw_pp)
                if bonus < 0: bonus = 0

                stars = []
                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    acc = (score.get("accuracy", 1.0) * 100)
                    combo = score.get("combo", 0.0)
                    pp = score.get("pp", 0.0)
                    mods_str = score.get("mods", "")     
                    path = results.get(score['beatmap_id'], None)
                    score_stats = score.get("score_stats")
                    lazer = score.get("lazer")   

                    misses = score.get("misses", 0)
                    if miss_limit is not None and misses > miss_limit:
                        new_pp = pp
                        max_combo = combo
                        stars = score.get("stars", 0.0)  
                    else:
                        #neko API 
                        payload = {
                            "map_path": str(score.get('beatmap_id', "0")), 
                            
                            "n300": int(score_stats.get("count_300", 0)),
                            "n100": int(score_stats.get("count_100", 0)),
                            "n50": int(score_stats.get("count_50", 0)),
                            "misses": int(misses),                   
                            
                            "mods": str(score.get("mods", 0)), 
                            "combo": int(score.get("combo", 0.0)),      
                            "accuracy": float(score.get("accuracy", 1.0) * 100),    
                            
                            "lazer": bool(score.get('lazer', False)),          
                            "clock_rate": float(score.get('speed_multiplier') or 1.0),  

                            "custom_ar": float(score.get('AR', 0.0)),
                            "custom_cs": float(score.get('CS', 0.0)),
                            "custom_hp": float(score.get('HP', 0.0)),
                            "custom_od": float(score.get('OD', 0.0)),
                        }

                        try:
                            pp_data = await get_score_pp_neko_api(payload)

                            _pp = pp_data.get("pp")
                            max_pp = pp_data.get("no_choke_pp")
                            _perfect_pp = pp_data.get("perfect_pp")

                            stars = pp_data.get("star_rating")
                            max_combo = pp_data.get("perfect_combo")
                            _expected_bpm = pp_data.get("expected_bpm")

                        except Exception as e:
                            print(f"neko API failed: {e}")                     
                                                
                    score["index"] = i + 1
                    score["pp_old"] = pp
                    score["pp_new"] = max_pp
                    score["stars"] = stars
                    score["combo_old"] = combo
                    score["combo_max"] = max_combo
                  
                best_scores = sorted(
                    best_scores, 
                    key=lambda s: s.get("pp_new", 0), 
                    reverse=True
                )
                for i, score in enumerate(best_scores):
                    score["weight_percent"] = 0.95 ** i
                
                total_pp = 0
                for i, score in enumerate(best_scores):
                    weight = 0.95 ** i
                    total_pp += score.get("pp_new", 0) * weight
                new_total = total_pp + bonus

                best_scores = [s for s in best_scores if s.get("misses", 0) != 0]

                if isinstance(best_scores, list) and best_scores:
                    if miss_limit is not None:
                        best_scores = [s for s in best_scores if s.get("misses", 0) <= miss_limit]
                    page_size = 5
                    total_pages = (len(best_scores) + page_size - 1) // page_size

                context.user_data["best_scores"] = best_scores
                context.user_data["user_data"] = user_data
                context.user_data["total_pages"] = total_pages

                if "user_data" not in context.user_data:
                    context.user_data["user_data"] = {}

                context.user_data["user_data"]["live_pp"] = live_pp
                context.user_data["user_data"]["new_total"] = new_total

                page_size = 10
                total_pages = (len(best_scores) + page_size - 1) // page_size
                page = 0

                text = get_text(user_data, best_scores, page)
                keyboard = get_keyboard(page, total_pages, update.effective_user.id)
  
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )

                return
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при nochoke (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Непонятно... Попробуй еще раз через несколько секунд!`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )

# нигде не используется???

# async def show_scores_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     best_scores = context.user_data.get("best_scores", [])
#     user_data = context.user_data.get("user_data")
#     total_pages = context.user_data.get("total_pages", 1)

#     user_id = update.effective_user.id
#     page = 0
#     text = get_page_text_choke(user_data, best_scores, page)
#     keyboard = get_keyboard(page, total_pages, user_id)

#     await update.message.reply_text(
#         text=text,
#         parse_mode="HTML",
#         disable_web_page_preview=True,
#         reply_markup=keyboard
#     )
