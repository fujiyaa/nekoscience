


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
            "current_tier":             int(v1.get("current_tier", 1)),
            "points": {
                "previous_seasons":     int(v1.get("points", 0).get("previous_seasons", 0)),
                "current_season":       int(v1.get("points", 0).get("current_season", 0))
            },
            "active":                   v1.get("active", None),     # beatmapset
            "skipped":                  v1.get("skipped", {}),
            "completed":                v1.get("completed", {})
        }
    }

def construct_beatmapset(beatmapset_data, goal: str):
    return {               
        "beatmapset_id":    beatmapset_data.get("beatmapset_id"),

        "artist":           beatmapset_data.get("artist"),
        "title":            beatmapset_data.get("title"),
        "creator":          beatmapset_data.get("creator"),        
        "bg_url":           beatmapset_data.get("bg_url"),

        "goal": goal,                        
        "given": time.time()
    }
