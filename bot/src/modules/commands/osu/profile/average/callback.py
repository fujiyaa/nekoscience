


import traceback
import asyncio
from statistics import mean

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_query_answer, safe_edit_query
from .....external.osu_http import fetch_txt_beatmaps
from .....external.osu_api import get_user_scores
from .....utils.osu_conversions import apply_mods_to_stats, get_mods_info
from .....wrappers.average_table import get_average_table
from .....wrappers.user import get_user_link
from .....utils.calculate import caclulte_cached_entry, calculate_beatmap_attr
import temp

from config import USER_SETTINGS_FILE
from .....systems.translations import (
    DEFAULT_COMMAND_TEMPLATE as T,
    COMMAND_AVERAGE as AT,
)



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        uid_click = query.from_user.id
        
        parts = query.data.split(":")
        # average_select_type   :   u|c    :   {osu_username}  :   {value} :   osu
        action =        str(parts[1])
        origin_uid =    int(parts[2])        
        osu_username =  str(parts[3])
        scores_type =   str(parts[4])


        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(update.effective_user.id), {})
        lang = user_settings.get("lang", "ru")
                

        if uid_click != origin_uid:
                await safe_query_answer(
                    query, 
                    text = f"`{T.get('DEFAULT_INVALID_BUTTON_ORIGIN')[lang]}`",)
                
                return            
        await safe_query_answer(query, show_alert=False)    


        if action == "c":
            await safe_edit_query(
                query, 
                text = f"`{T.get('Canceled...')[lang]}`", 
                parse_mode = "Markdown"
            )

            # await delete_message_after_delay(
            #         context, 
            #         update.effective_chat.id, 
            #         update.effective_message.id, 
            #         delay = 5
            #     )
            
            return
        
        elif action == "u":                 
            await safe_edit_query(
                query, 
                text=f"`{T.get('Loading...')[lang]}`", 
                parse_mode="Markdown"
            )                         
            
            fails = user_settings.get("display_fails_average_recent", True)
            if fails: fails = 1

            recent_scores = await asyncio.wait_for(
                get_user_scores(
                    username = osu_username, 
                    limit = 100, 
                    fails = fails,
                    select = scores_type
                ),
                    
                timeout=10
            )
                
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
                    f'<code>{AT.get(scores_type)[lang]}</code>  <b>{len(recent_scores)}</b>  '  
                    f'<code>{AT.get("plays")[lang]}:</code>\n'
                    f'\n'
                    f'<pre>{table}</pre>'
                )          

                try:
                    await safe_edit_query(
                        query, 
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
                await safe_edit_query(
                    query, 
                    text=f"`{T.get('No data...')[lang]}`", 
                    parse_mode="Markdown"
                )
                return
            
    except Exception:
        traceback.print_exc() 
