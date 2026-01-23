


from ..utils.osu_conversions import is_legacy_score
from ..external.localapi import get_pp_parts_neko_api
from ..external.osu_http import fetch_txt_beatmaps



async def get_skills_by_scores(scores: dict = {}) -> dict | bool:
    """
    Один или несколько скоров -> pp_parts | False

    """
    payload = await _scores_to_payload(scores)
    
    if payload:
        payload = {
            "mode": "Osu",
            "scores": payload
        }

        try:
            skills = await get_pp_parts_neko_api(payload)

        except Exception as e:
            print(f"error calling Rust API: {e}")
    
        return {
            "weighted":{
                "acc": skills["acc"],
                "aim": skills["aim"],
                "speed": skills["speed"],
            },
            "raw":{
                "acc": skills["acc_total"],
                "aim": skills["aim_total"],
                "speed": skills["speed_total"],
            }        
        }
    
    else:
        return False

async def _get_beatmaps(scores: dict = {}) -> bool:

    maps_ids = []
    for score in scores:
        map_id = score["beatmap"]["id"]
        maps_ids.append(map_id)

    _results, failed = await fetch_txt_beatmaps(maps_ids)

    if failed:
        print("err loading maps (skills):", failed)   
        return False
    
    return True

async def _scores_to_payload(scores: dict = {}) -> dict | bool:

    if await _get_beatmaps(scores):    
        payload = []
        for score in scores:        
            if is_legacy_score(score): 
                lazer = False 
            else: 
                lazer = True            
            score["lazer"] = lazer          
            stats = score["statistics"]

            payload.append({
                "map_id": score["beatmap"]["id"],
                "n320": stats.get("count_geki", 0),
                "n300": stats.get("count_300", 0),
                "n200": stats.get("count_katu", 0),
                "n100": stats.get("count_100", 0),
                "n50":  stats.get("count_50", 0),
                "misses": stats.get("count_miss", 0),
                "combo": score.get("max_combo"),
                "mods": str(score.get("mods", "")),
                "accuracy": float(score["accuracy"] * 100.0),
                "set_on_lazer": bool(score.get("lazer", True)),
                "large_tick_hit": stats.get("count_large_tick_hit", 0),
                "small_tick_hit": stats.get("count_small_tick_hit", 0),
                "small_tick_miss": stats.get("count_small_tick_miss", 0),
                "slider_tail_hit": stats.get("count_slider_tail_hit", 0),
            })

        return payload
    
    else: 
        return False
