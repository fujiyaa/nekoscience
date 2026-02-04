


import asyncio
from statistics import mean

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....external.osu_http import fetch_txt_beatmaps
from ....external.osu_api import get_user_scores
from ....systems.auth import check_osu_verified
from ....utils.osu_conversions import apply_mods_to_stats, get_mods_info
from ....wrappers.average_table import get_average_table
from ....wrappers.user import get_user_link
from ....utils.calculate import caclulte_cached_entry, calculate_beatmap_attr
import temp

from config import COOLDOWN_STATS_COMMANDS, USER_SETTINGS_FILE



async def start_average_recent(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(average_recent(update, context, user_request))
async def average_recent(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
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

    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/average_recent fujina123` <- никнейм\n\n\n"
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
            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(update.effective_user.id), {}) 
            fails = user_settings.get("display_fails_average_recent", True)
            _lang = user_settings.get("lang", "ru") 
            
            if fails: fails = 1

            recent_scores = await asyncio.wait_for(get_user_scores(username, limit=100, fails=fails), timeout=10)
                  
            if isinstance(recent_scores, list) and recent_scores: 
                accs, combos, misses, pps = [], [], [], []
                stars, ars, css, hps, ods, bpms, lengths = [], [], [], [], [], [], []

                # beatmap_requests = []
                # for score in recent_scores:
                #     beatmap_requests.append({
                #         "beatmap_id": score.get("beatmap_id"),
                #         "mods": score.get("mods", []),
                #         "ruleset_id": 0  # osu ruleset
                #     })

                # attributes_list = await get_beatmap_attributes_batch(beatmap_requests, token=token, parallel_limit=5, delay_between_batches=0.1)

                maps_ids = []
                for cached_entry in recent_scores:                    
                    maps_ids.append(cached_entry['map']['beatmap_id'])

                _results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_recent):", failed)

                for cached_entry in recent_scores:
                    map =               cached_entry['map']
                    osu_score =         cached_entry['osu_score']
                    neko_api_calc =     cached_entry['neko_api_calc']

                    if not cached_entry['state']['calculated']:
                        await caclulte_cached_entry(cached_entry)
                        
                        neko_api_calc = cached_entry['neko_api_calc']
                     
                    pp = neko_api_calc.get("pp")

                     #temp pp fix
                    pp = pp if not isinstance(osu_score.get("pp"), (int, float)) or osu_score.get("pp") <= 0 else osu_score.get("pp")
                          
                    base_values = await calculate_beatmap_attr(cached_entry)

                    bpm = (map.get("bpm", 0.0))
                    length = (map.get("hit_length", 0))                    
                    mods_str = osu_score.get("mods", "")
                    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)                    
                    length = int(round(float(length) / speed_multiplier))
                   
                    bpm, ar, od, cs, hp = apply_mods_to_stats(
                        bpm, base_values[0], base_values[2], base_values[1], base_values[3],
                        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                    )

                    pps.append(pp)
                    accs.append(osu_score.get('accuracy', 0.0) * 100)
                    combos.append(osu_score.get("max_combo", 0))
                    misses.append(osu_score.get("count_miss", 0))                    
                    stars.append(neko_api_calc.get("star_rating") or 0) 
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

                user_link = get_user_link(recent_scores[0])
                table = get_average_table(table_data)     

                text=(
                    f'{user_link}\n'
                    f'\n'
                    f'<code>Из последних</code>  <b>{len(recent_scores)}</b>  <code>игр:</code>\n'
                    f'\n'
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
                    text="`Нет данных`",
                    parse_mode="Markdown"
                )
                return

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при average_recent (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
