


import asyncio
import temp

from ....actions.messages import safe_send_message, try_send
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_top_100_scores
from ....external.osu_http import beatmap
from ....external.localapi import get_score_pp_neko_api
from ....utils.osu_conversions import calculate_weighted_pp, insert_pp
from ....utils.text_format import normalize_no_plus, country_code_to_flag

from config import USER_SETTINGS_FILE
from ....systems.translations import TRANSLATIONS as TR



async def send_score_fix(update, score, user_id, token:str = None):    
    
    path, base_values = await beatmap(score['beatmap']['id'])    
    score_stats = score.get("score_stats", score.get("statistics")) 

    base_ar = score.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = score.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = score.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = score.get("DA_values", {}).get("drain_rate", base_values["hp"])          
    
    #neko API 
    payload = {
        "map_path": str(score['beatmap']['id']), 
        
        "n300": score_stats.get("count_300", None),
        "n100": score_stats.get("count_100", None),
        "n50": score_stats.get("count_50", None),
        "misses": int(score['count_miss']),                   
        
        "mods": str(score.get("mods", 0)), 
        "combo": int(score['max_combo']),      
        "accuracy": float(score['accuracy']*100),    
        
        "lazer": bool(score.get('lazer', False)),          
        "clock_rate": float(score.get('speed_multiplier') or 1.0),  

        "custom_ar": float(base_ar),
        "custom_cs": float(base_cs),
        "custom_hp": float(base_hp),
        "custom_od": float(base_od),
    }

    try:
        pp_data = await get_score_pp_neko_api(payload)

        pp = pp_data.get("pp")
        max_pp = pp_data.get("no_choke_pp")
        _perfect_pp = pp_data.get("perfect_pp")

        _stars = pp_data.get("star_rating")
        _perfect_combo = pp_data.get("perfect_combo")
        _expected_bpm = pp_data.get("expected_bpm")

    except Exception as e:
        print(f"neko API failed: {e}")
    
    
    mods_str = score.get("mods", "")
    mods_text = normalize_no_plus(mods_str)
    try:
        best_pp = await asyncio.wait_for(get_top_100_scores(score['user']['username'], token, score['user']['id']), timeout=10, )        
    except:
        return

    live_raw_pp = calculate_weighted_pp(best_pp, bonus_pp=0)
    map_pp = float(f"{max_pp:.3f}")

    try:
        pos, new_best_pp = insert_pp(best_pp, map_pp, '')
    except:
        pos = None

    username = score['user']['username']
    total_pp, global_rank, country_rank, country_code = score['total_pp'], score['global_rank'], score['country_rank'], score['country_code']
    pp_text = f"{total_pp}"
    country_rank_text = (
        f"  {country_code}#{country_rank:,})"
    )
    rank_text = f"{username}: {pp_text}pp (#{global_rank}{country_rank_text}"
    country_flag = country_code_to_flag(country_code)
    user_link = f'{country_flag} <b>{rank_text}</b>'  

    pp_int, pp_frac = str(f"{pp:.2f}").split(".")
    max_pp_int, max_pp_frac = str(f"{max_pp:.2f}").split(".")
    
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   

    
    if pos is not None and pos<101:
        live_pp = total_pp
        bonus =  float(live_pp) - float(live_raw_pp)
        if bonus < 0: bonus = 0

        new_total = calculate_weighted_pp(new_best_pp, bonus)
        best_text =(
            f"{TR['r_fix_it_would'][lang_code]}<b>#{pos+1}</b>{TR['r_fix_in_top_100'][lang_code]}<b>{new_total:.2f}pp</b>."
        )    
    else:
        best_text =(
            f"\n{TR['r_fix_top100'][lang_code]}."
        ) 

    caption = (
        f"{user_link}\n\n"
        f'{mods_text} <b>FC</b>{TR["r_fix_improve"][lang_code]}<a href="{score["url"]}">{TR["r_fix_the_score"][lang_code]}</a>'
        f"{TR['r_fix_from'][lang_code]}<u>{pp_int}</u>.{pp_frac} "
        f"{TR['r_fix_to'][lang_code]}<b><u>{max_pp_int}</u>.{max_pp_frac}рр</b>.{best_text}"
        f"\n⠀"
    )        
    
    return await update.message.reply_text(text=caption, parse_mode="HTML")
