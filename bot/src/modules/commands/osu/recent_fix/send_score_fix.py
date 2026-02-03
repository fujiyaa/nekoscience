


import asyncio
import temp
from datetime import datetime

from ....external.osu_api import get_top_100_scores
from ....external.osu_http import beatmap
from ....external.localapi import get_score_pp_neko_api
from ....utils.osu_conversions import calculate_weighted_pp, insert_pp
from ....utils.text_format import country_code_to_flag
from modules.systems.json_files import save_score_file
from ....utils import text_format
from ....external.osu_http import beatmap
from ....utils.osu_conversions import get_mods_info

from config import USER_SETTINGS_FILE
from ....systems.translations import TRANSLATIONS as TR



async def send_score_fix(update, cached_entry, user_id, token:str = None):    
    user =              cached_entry['user']
    map =               cached_entry['map']
    osu_api_data =      cached_entry['osu_api_data']
    osu_score =         cached_entry['osu_score']
    neko_api_calc =     cached_entry['neko_api_calc']
    lazer_data =        cached_entry['lazer_data']
    state =             cached_entry['state']
    meta =              cached_entry['meta']
    
    lazer = state.get('lazer')
    
    acc = osu_score.get('accuracy')

    mods_str = osu_score.get("mods", "")
    mods_text = text_format.normalize_no_plus(mods_str)
    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

    map_id = map.get('beatmap_id')
    _path, base_values = await beatmap(int(map_id))

    # карты без ar
    base_values["ar"] = map.get("ar", 5) if base_values.get("ar") is None else base_values["ar"]
    
    if not isinstance(lazer_data.get("DA_values"), dict):
        lazer_data["DA_values"] = {}

    base_ar = lazer_data.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = lazer_data.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = lazer_data.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = lazer_data.get("DA_values", {}).get("drain_rate", base_values["hp"])
    
    #neko API 
    payload = {
        "map_path": str(map_id), 
        
        "n300": osu_score.get("count_300", None),
        "n100": osu_score.get("count_100", None),
        "n50": osu_score.get("count_50", None),
        "misses": osu_score.get('count_miss'),                   
        
        "mods": str(osu_score.get("mods", 0)), 
        "combo": int(osu_score['max_combo']),      
        "accuracy": float(acc*100),    
        
        "lazer": bool(lazer),          
        "clock_rate": float(lazer_data.get('speed_multiplier') or 1.0),  

        "custom_ar": float(base_ar),
        "custom_cs": float(base_cs),
        "custom_hp": float(base_hp),
        "custom_od": float(base_od),
    }

    try:
        pp_data = await get_score_pp_neko_api(payload)

        pp = pp_data.get("pp")
        max_pp = pp_data.get("no_choke_pp")
        perfect_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        perfect_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

        cached_entry.update(
            {
                "neko_api_calc": {
                    "pp":               pp,
                    "no_choke_pp":      max_pp,
                    "perfect_pp":       perfect_pp,

                    "star_rating":      stars,
                    "perfect_combo":    perfect_combo,
                    "expected_bpm":     expected_bpm,
                },
            }
        )
        cached_entry.setdefault("state", {}).update({"calculated": True})
        cached_entry.setdefault("meta", {}).update({"calculated_at": datetime.now().isoformat()})
        
        if cached_entry['state']['calculated']:
            cached_entry.setdefault("state", {}).update({"ready": True})
        else:
            cached_entry.setdefault("state", {}).update({"error": True})
            
        save_score_file(cached_entry['osu_api_data']['id'], cached_entry)
        
    except Exception as e:
        print(f"neko API failed: {e}")

    if cached_entry['state']['error']:
        return None # ???
        
    try:
        best_pp = await asyncio.wait_for(get_top_100_scores(user.get('username'), token, osu_score.get('user_id')), timeout=10, )        
    except:
        return

    live_raw_pp = calculate_weighted_pp(best_pp, bonus_pp=0)
    map_pp = float(f"{max_pp:.3f}")

    try:
        pos, new_best_pp = insert_pp(best_pp, map_pp, '')
    except:
        pos = None

    username = user.get("username")
    total_pp, global_rank, country_rank, country_code = user.get('total_pp', '0'), user.get('global_rank'), user.get('country_rank'), user.get('country_code')
    pp_text = f"{total_pp}"
    country_rank_text = (
        f"  {country_code}#{country_rank:,})"
    )
    rank_text = f"{username}: {pp_text}pp (#{global_rank}{country_rank_text}"
    country_flag = country_code_to_flag(country_code)
    user_link = f'<a href="https://osu.ppy.sh/users/{osu_score.get("user_id")}">{country_flag} <b>{rank_text}</b></a>' 

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
    
    if lazer: 
        is_cl = ""
    else: 
        is_cl = "(Stable)"

    mods_lazer = text_format.normalize_no_plus(mods_str)     
    mods_text = f'{mods_lazer}{is_cl}' 

    score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"

    caption = (
        f"{user_link}\n\n"
        f'{mods_text} <b>FC</b>{TR["r_fix_improve"][lang_code]}<a href="{score_url}">{TR["r_fix_the_score"][lang_code]}</a>'
        f"{TR['r_fix_from'][lang_code]}<u>{pp_int}</u>.{pp_frac} "
        f"{TR['r_fix_to'][lang_code]}<b><u>{max_pp_int}</u>.{max_pp_frac}рр</b>.{best_text}"
        f"\n⠀"
    )        
    
    return await update.message.reply_text(text=caption, parse_mode="HTML")
