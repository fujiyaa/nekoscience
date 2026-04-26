import traceback
import asyncio
from statistics import mean
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_query_answer, safe_edit_query
from .....external.osu_http import fetch_txt_beatmaps
from .....external.osu_api import get_user_scores
from .....utils.osu_conversions import apply_mods_to_stats, get_mods_info
from .....wrappers.average_table import get_average_table
from .....wrappers.minmax_table import get_minmax_table
from .....wrappers.user import get_user_link
from .....wrappers.ppfire import get_fire_text
from .....utils.calculate import caclulte_cached_entry, calculate_beatmap_attr
import temp

from config import USER_SETTINGS_FILE
from .....systems.translations import (
    DEFAULT_COMMAND_TEMPLATE as T,
    COMMAND_AVERAGE as AT,
    DEFAULT_SCORES_PROP as SP
)


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        uid_click = query.from_user.id
        
        parts = query.data.split(":")
        action =        str(parts[1])
        origin_uid =    int(parts[2])        
        osu_username =  str(parts[3])
        scores_type =   str(parts[4])
        k_type =        str(parts[6])

        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(update.effective_user.id), {})
        lang = user_settings.get("lang", "ru")
                
        if uid_click != origin_uid:
            await safe_query_answer(
                query, 
                text=f"`{T.get('DEFAULT_INVALID_BUTTON_ORIGIN')[lang]}`",
            )
            return            

        await safe_query_answer(query, show_alert=False)    

        # cancel
        if action == "c":
            await safe_edit_query(
                query, 
                text=f"`{T.get('Canceled...')[lang]}`", 
                parse_mode="Markdown"
            )
            return

        # ===============================
        # ЗАГРУЗКА СКОРОВ (общая часть)
        # ===============================
        elif action in ["u", "f"]:
            await safe_edit_query(
                query, 
                text=f"`{T.get('Loading...')[lang]}`", 
                parse_mode="Markdown"
            )                         

            fails = user_settings.get("display_fails_average_recent", True)
            if fails:
                fails = 1

            select_type = scores_type if action == "u" else "best"

            recent_scores = await asyncio.wait_for(
                get_user_scores(
                    username=osu_username, 
                    limit=100, 
                    fails=fails,
                    select=select_type
                ),
                timeout=10
            )

            if not (isinstance(recent_scores, list) and recent_scores):
                await safe_edit_query(
                    query, 
                    text=f"`{T.get('No data...')[lang]}`", 
                    parse_mode="Markdown"
                )
                return

            # ===============================
            # 🔥 РЕЖИМ "КОСТЁР"
            # ===============================
            if action == "f":
                now = datetime.now(timezone.utc)

                # период
                if scores_type == "1m":
                    days = 30
                elif scores_type == "2m":
                    days = 60
                elif scores_type == "3m":
                    days = 90
                else:
                    days = 30

                period_text = {
                    "1m": "1 месяц",
                    "2m": "2 месяца",
                    "3m": "3 месяца"
                }.get(scores_type, "1 месяц")

                month_ago = now - timedelta(days=days)

                total_pp = 0.0
                count = 0
                pp_list = []

                for cached_entry in recent_scores:
                    date_str = cached_entry['osu_api_data'].get('date')
                    if not date_str:
                        continue

                    try:
                        created_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except:
                        continue

                    if created_at < month_ago:
                        continue

                    osu_score = cached_entry['osu_score']
                    neko_api_calc = cached_entry['neko_api_calc']

                    if not cached_entry['state']['calculated']:
                        await caclulte_cached_entry(cached_entry)
                        neko_api_calc = cached_entry['neko_api_calc']

                    pp = neko_api_calc.get("pp")

                    if isinstance(osu_score.get("pp"), (int, float)) and osu_score.get("pp") > 0:
                        pp = osu_score.get("pp")

                    if isinstance(pp, (int, float)):
                        total_pp += pp
                        count += 1
                        pp_list.append(pp)

                raw_pp = total_pp

                pp_list.sort(reverse=True)

                weighted_pp = 0.0
                for i, pp in enumerate(pp_list):
                    weighted_pp += pp * (0.95 ** i)


                user = recent_scores[0].get('user')    
                live_total_pp =  user.get('total_pp', '0')

                user_link = get_user_link(recent_scores[0])

                table = get_fire_text(
                    period_text=period_text,
                    days=days,
                    total_scores=len(pp_list),
                    filtered_scores=pp_list,
                    raw_pp=raw_pp,
                    weighted_pp=weighted_pp,
                    user_total_pp=float(live_total_pp)
                )

                burned_pp = live_total_pp - weighted_pp

                burn_line = (
                    f"\n\n{period_text} 🔥 "
                    f"сгорело <b>{burned_pp:.2f}pp</b>, "
                    f"{live_total_pp:.2f} → {weighted_pp:.2f} pp (не считая бонусных)"
                )

                text = f"{user_link}\n\n{table}{burn_line}"

                await safe_edit_query(
                    query,
                    text=text,
                    parse_mode="HTML"
                )
                return

            # ===============================
            # СТАРАЯ ЛОГИКА (НЕ ТРОГАЕМ)
            # ===============================
            accs, combos, misses, pps = [], [], [], []
            stars, ars, css, hps, ods, bpms, lengths = [], [], [], [], [], [], []

            maps_ids = []
            for cached_entry in recent_scores:                    
                maps_ids.append(cached_entry['map']['beatmap_id'])

            _results, failed = await fetch_txt_beatmaps(maps_ids)

            if failed:
                print("err loading maps (average_recent):", failed)

            use_ids = (k_type == "2")

            for cached_entry in recent_scores:
                map =               cached_entry['map']
                osu_score =         cached_entry['osu_score']
                neko_api_calc =     cached_entry['neko_api_calc']
                score_id =          cached_entry['osu_api_data']['id']

                if not cached_entry['state']['calculated']:
                    await caclulte_cached_entry(cached_entry)
                    neko_api_calc = cached_entry['neko_api_calc']
                
                pp = neko_api_calc.get("pp")

                if isinstance(osu_score.get("pp"), (int, float)) and osu_score.get("pp") > 0:
                    pp = osu_score.get("pp")
                    
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

                if use_ids:
                    pps.append((pp, score_id))
                    accs.append(((osu_score.get('accuracy') or 0) * 100, score_id))
                    combos.append((osu_score.get("max_combo") or 0, score_id))
                    misses.append((osu_score.get("count_miss") or 0, score_id))
                    stars.append((neko_api_calc.get("star_rating") or 0, score_id))
                    ars.append((ar, score_id))
                    css.append((cs, score_id))
                    hps.append((hp, score_id))
                    ods.append((od, score_id))
                    bpms.append((bpm, score_id))
                    lengths.append((length, score_id))
                else:
                    pps.append(pp)
                    accs.append((osu_score.get('accuracy') or 0) * 100)
                    combos.append(osu_score.get("max_combo") or 0)
                    misses.append(osu_score.get("count_miss") or 0)
                    stars.append(neko_api_calc.get("star_rating") or 0)
                    ars.append(ar)
                    css.append(cs)
                    hps.append(hp)
                    ods.append(od)
                    bpms.append(bpm)
                    lengths.append(length)
                                
            if use_ids:
                def calc_stats(values):
                    numeric_values = [(v, sid) for v, sid in values if isinstance(v, (int, float))]
                    if not numeric_values:
                        return (("-", "-"), ("-", "-"))

                    min_v, min_id = min(numeric_values, key=lambda x: x[0])
                    max_v, max_id = max(numeric_values, key=lambda x: x[0])

                    return ((min_v, min_id), (max_v, max_id))
            else:
                def calc_stats(values):
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    if not numeric_values:
                        return ("-", "-", "-")
                    return (min(numeric_values), mean(numeric_values), max(numeric_values))      

            table_data = {                    
                SP.get('Accuracy')[lang]:   calc_stats(accs),
                SP.get('Combo')[lang]:      calc_stats(combos),
                SP.get('Misses')[lang]:     calc_stats(misses),
                SP.get('Stars')[lang]:      calc_stats(stars),
                SP.get('PP')[lang]:         calc_stats(pps),
                SP.get('AR')[lang]:         calc_stats(ars),
                SP.get('CS')[lang]:         calc_stats(css),
                SP.get('HP')[lang]:         calc_stats(hps),
                SP.get('OD')[lang]:         calc_stats(ods),
                SP.get('BPM')[lang]:        calc_stats(bpms),
                SP.get('Length')[lang]:     calc_stats(lengths),
            }

            user_link = get_user_link(recent_scores[0])

            if use_ids:
                table = get_minmax_table(table_data, lang)
                text=(f'{user_link}\n\n{table}')
            else:
                table = get_average_table(table_data, lang)
                text=(f'{user_link}\n\n<pre>{table}</pre>')

            await safe_edit_query(
                query, 
                text=text, 
                parse_mode="HTML"
            )

    except Exception:
        traceback.print_exc()