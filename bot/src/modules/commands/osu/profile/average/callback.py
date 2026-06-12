import traceback
import asyncio
from statistics import mean
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_query_answer, safe_edit_query
from .....actions.rich import edit_rich_query
from .....external.osu_http import fetch_txt_beatmaps
from .....external.osu_api import get_user_scores
from .....utils.osu_conversions import apply_mods_to_stats, get_mods_info
from .....wrappers.average_table import get_average_table
from .....wrappers.minmax_table import get_minmax_table
from .....wrappers.user import get_user_link
from .....wrappers.ppfire import get_fire_text
from .....wrappers.userlink_rich import get_rich_userlink_from_entry
from .....utils.calculate import caclulte_cached_entry, calculate_beatmap_attr
import temp

from config import USER_SETTINGS_FILE
from .....systems.translations import (
    TRANSLATIONS as TRA,
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

                user_link = get_rich_userlink_from_entry(recent_scores[0])

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
                text = f"""
{user_link}

{table}

<details><summary> за {period_text} 🔥 сгорело <b>{burned_pp:.2f}pp</b>, <s>{live_total_pp:.2f}</s> → {weighted_pp:.2f}pp</summary>

<b>⚙️ Механика</b>
- Берутся скоры из топ100
- Остаются только выбранные (30 / 60 / 90 дней)
- Скоры взвшешиваются заново в новом топе
- PP костра = Текущее РР, если бы скоров вне таймера не существовало

<b>Обозначения по шкале:</b>
- 🟢 игрок геймер
- 🟡 норм
- 🟠🔴 зона опасности
- ❗️💀 почти не осталось РР
</details>
"""

                # await safe_edit_query(
                #     query,
                #     text=text,
                #     parse_mode="HTML"
                # )

                await edit_rich_query(
                    query,
                    markdown=text
                )

                return

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
                                
            def calc_stats(key, values):
                numeric_values = [(v, sid) for v, sid in values if isinstance(v, (int, float))] \
                    if use_ids else [(v, None) for v in values if isinstance(v, (int, float))]

                if not numeric_values:
                    return (("-", "-"), ("-", "-")) if use_ids else ("-", "-", "-")

                min_v, min_id = min(numeric_values, key=lambda x: x[0])
                max_v, max_id = max(numeric_values, key=lambda x: x[0])
                avg_v = sum(v for v, _ in numeric_values) / len(numeric_values)

                def format_value(v):
                    if key == "Length":
                        return _format_time(v)

                    return smart_format(v)

                def fmt(v, sid=None, is_min=False, is_max=False):
                    v_str = format_value(v)

                    if use_ids:
                        return (f"{v_str} 🔗", sid)

                    if is_max:                        
                        v_str = f"<b>{v_str}</b>"
                    elif is_min:
                        v_str = f"<code>{v_str}</code>"                    

                    return v_str

                if use_ids:
                    return (
                        fmt(min_v, min_id, is_min=True),
                        fmt(max_v, max_id, is_max=True)
                    )

                return (
                    fmt(min_v, is_min=True),
                    fmt(avg_v),
                    fmt(max_v, is_max=True)
                )

            table_data = {
                SP.get('Accuracy')[lang]: calc_stats('Accuracy', accs),
                SP.get('Combo')[lang]:    calc_stats('Combo', combos),
                SP.get('PP')[lang]:       calc_stats('PP', pps),
                SP.get('Misses')[lang]:   calc_stats('Misses', misses),
                SP.get('Stars')[lang]:    calc_stats('Stars', stars),
                SP.get('Length')[lang]:   calc_stats('Length', lengths),

                SP.get('BPM')[lang]:      calc_stats('BPM', bpms),
                SP.get('AR')[lang]:       calc_stats('AR', ars),
                SP.get('CS')[lang]:       calc_stats('CS', css),
                SP.get('HP')[lang]:       calc_stats('HP', hps),
                SP.get('OD')[lang]:       calc_stats('OD', ods),
            }

            user_link = get_rich_userlink_from_entry(recent_scores[0])

            if use_ids:
                core_table, stat_table = get_minmax_table(table_data, lang, split_index=6)
                text= f"""
{user_link}

<code>{AT.get(scores_type)[lang]}</code>  <b>{len(recent_scores)}</b>  <code>{AT.get("plays")[lang]}:</code>

{core_table}

<details><summary>{TRA.get("...5 more")[lang]}</summary>
{stat_table}

</details>
"""                
            else:
                core_table, stat_table = get_average_table(table_data, lang, split_index=6)
                text= f"""
{user_link}

<code>{AT.get(scores_type)[lang]}</code>  <b>{len(recent_scores)}</b>  <code>{AT.get("plays")[lang]}:</code>

{core_table}

<details><summary>{TRA.get("...5 more")[lang]}</summary>
{stat_table}

</details>
"""

            # await safe_edit_query(
            #     query, 
            #     text=text, 
            #     parse_mode="HTML"
            # )

            await edit_rich_query(
                query,
                markdown=text
            )

    except Exception:
        traceback.print_exc()

def _format_time(seconds):
    if isinstance(seconds, str):
        return seconds
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def smart_format(v):
    if isinstance(v, str):
        return v

    if isinstance(v, int):
        return str(v)

    if isinstance(v, float):
        # убираем хвостовые нули
        s = f"{v:.2f}".rstrip("0").rstrip(".")

        # если стало пусто → это 0.00
        return s if s else "0"

    return str(v)