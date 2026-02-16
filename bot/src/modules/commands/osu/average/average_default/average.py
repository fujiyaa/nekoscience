


import asyncio
from statistics import mean

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....external.osu_http import fetch_txt_beatmaps
from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .....external.localapi import get_map_stats_neko_api
from .....systems.auth import check_osu_verified
from .....utils.text_format import country_code_to_flag
from .....utils.osu_conversions import apply_mods_to_stats, get_mods_info
from .....wrappers.average_table import get_average_table

from config import COOLDOWN_STATS_COMMANDS



async def start_average_stats(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(average_stats(update, context, user_request))
async def average_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
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
    MAX_ATTEMPTS = 3 

    user_id = str(update.message.from_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/average_stats fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", 
        parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
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
                accs, combos, misses, pps = [], [], [], []
                stars, ars, css, hps, ods, bpms, lengths = [], [], [], [], [], [], []

                # beatmap_requests = []
                # for score in best_scores:
                #     beatmap_requests.append({
                #         "beatmap_id": score.get("beatmap_id"),
                #         "mods": score.get("mods", []),
                #         "ruleset_id": 0  # osu ruleset
                #     })

                # attributes_list = await get_beatmap_attributes_batch(beatmap_requests, token=token, parallel_limit=5, delay_between_batches=0.1)

                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                _results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    accs.append(score.get("accuracy", 0.0) * 100)
                    combos.append(score.get("combo", 0))
                    misses.append(score.get("misses", 0))
                    pps.append(score.get("pp", 0.0))
                    ar = (score.get("AR", 0.0))
                    cs = (score.get("CS", 0.0))
                    hp = (score.get("HP", 0.0))
                    od = (score.get("OD", 0.0))
                    bpm = (score.get("bpm", 0.0))
                    length = (score.get("length", 0))
                    
                    mods_str = score.get("mods", "")
                    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)
                   
                    #neko API 
                    payload = {
                        "map_path": str(score.get('beatmap_id', "0")), 
                        
                        "n300": 0,
                        "n100": 0,
                        "n50": 0,
                        "misses": 0,                   
                        
                        "mods": str(mods_str), 
                        "combo": int(0),      
                        "accuracy": float(0.0),    
                        
                        "lazer": bool(True),          
                        "clock_rate": float(1.0),  

                        "custom_ar": float(ar),
                        "custom_cs": float(cs),
                        "custom_hp": float(hp),
                        "custom_od": float(od),
                    }

                    try:
                        pp_data = await get_map_stats_neko_api(payload)

                        map_stars = pp_data.get("star_rating")                     
                        
                    except Exception as e:
                        print(f"neko API failed: {e}")

                    stars.append(map_stars)

                    # print(map_stars, str(score.get('beatmap_id', "0")))

                    bpm, ar, od, cs, hp = apply_mods_to_stats(
                        bpm, ar, od, cs, hp,
                        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                    )
                    length = int(round(float(length) / speed_multiplier))

                    ars.append(ar)
                    css.append(cs)
                    hps.append(hp)
                    ods.append(od)
                    bpms.append(bpm)
                    lengths.append(length)
                                    
                def calc_stats(values):
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    if not numeric_values:
                        return ("-", "-", "-")
                    return (min(numeric_values), mean(numeric_values), max(numeric_values))                

                table_data = {
                    "Accuracy": calc_stats(accs),
                    "Combo": calc_stats(combos),
                    "Misses": calc_stats(misses),
                    "Stars": calc_stats(stars),
                    "PP": calc_stats(pps),
                    "AR": calc_stats(ars),
                    "CS": calc_stats(css),
                    "HP": calc_stats(hps),
                    "OD": calc_stats(ods),
                    "BPM": calc_stats(bpms),
                    "Length": calc_stats(lengths),
                }

                # user_link = get_user_link(recent_scores[0])
                table = get_average_table(table_data)     

                text=(
                    # f'{user_link}\n'
                    # f'\n'
                    # f'<code>Из последних</code>  <b>{len(recent_scores)}</b>  <code>игр:</code>\n'
                    # f'\n'
                    f'<pre>{table}</pre>'
                )              


                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"            
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Нет данных о топ100`",
                    parse_mode="Markdown"
                )
                return

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при average_stats (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
