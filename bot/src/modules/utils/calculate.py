


from datetime import datetime

from ..external import localapi
from ..external.osu_http import beatmap
from modules.systems.json_files import save_score_file
from ..systems import scores_state_db as db



# опечатка каклюльт
async def caclulte_cached_entry(cached_entry: dict): 
    map =               cached_entry['map']
    osu_score =         cached_entry['osu_score']
    lazer_data =        cached_entry['lazer_data']
    state =             cached_entry['state']

    lazer = state.get('lazer')
    acc = osu_score.get('accuracy')    
    map_id = map.get('beatmap_id')    
    base_values = await calculate_beatmap_attr(cached_entry)
    
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

        "custom_ar": float(base_values[0]),
        "custom_cs": float(base_values[1]),        
        "custom_od": float(base_values[2]),
        "custom_hp": float(base_values[3]),
    }

    try:
        pp_data = await localapi.get_score_pp_neko_api(payload)

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

        # база для миниигр со скорами
        db.add_score(cached_entry)
        
    except Exception as e:
        print(f"neko API failed: {e}")
        return None

    if cached_entry['state']['error']:
        print("Error: cached_entry state error")
        return None
    
    return cached_entry          

async def calculate_beatmap_attr(cached_entry: dict) -> tuple[float, float, float, float]:
    map =               cached_entry['map']
    lazer_data =        cached_entry['lazer_data']

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

    adjusted_values = float(base_ar), float(base_cs), float(base_od), float(base_hp)
    
    return adjusted_values
