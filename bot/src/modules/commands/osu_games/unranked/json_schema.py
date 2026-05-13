


import time



def construct_user(osu_id: int, osu_name: str, tg_id: int, tg_name: str, v1: dict = None):
    if v1 is None: v1 = {}

    return {
        "osu":{
            "username":     str(osu_name),
            "id":           int(osu_id)
        },
        
        "telegram":{
            "username":     str(tg_name),                    
            "id":           int(tg_id),
        },

        "v1": {            
            "points": {
                "current_score":        int(v1.get("points", {}).get("current_score", 0)),
                "average_score":        int(v1.get("points", {}).get("average_score", 0)),
                "best_score":           int(v1.get("points", {}).get("best_score", 0)),

                "current_health":       int(v1.get("points", {}).get("current_health", 0))
            },
            "active":                   v1.get("active", None),     # construct_active
            "skipped":                  v1.get("skipped", {}),
            "completed":                v1.get("completed", {})
        }
    }

def construct_active(cached_entries: list [dict], value_to_guess: str, user_msg_id: str, bot_msg_id: str):
    
    scores_ids = []

    for entry in cached_entries:
       scores_ids.append(entry.get('osu_api_data', {}).get('id', 0))

    return {
        "scores_ids":           scores_ids,

        "origin_user_msg_id":   user_msg_id,
        "origin_bot_msg_id":    bot_msg_id,

        "value_to_guess":       value_to_guess,

        "given":                time.time()
    }
