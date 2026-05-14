


import time



def construct_user(
    osu_id: int, 
    osu_name: str, 
    tg_id: int, 
    tg_name: str, 
    v1: dict = None,
    config: dict = None,
    intake: dict = None
):
    if v1 is None: v1 = {}
    if config is None: config = construct_config()
    if intake is None: intake = {}

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
                "current":              int(v1.get("points", {}).get("current", 1000)),
                "min":                  int(v1.get("points", {}).get("min", 1000)),
                "max":                  int(v1.get("points", {}).get("max", 1000)),
            },
            "active":                   v1.get("active", None),     # construct_active            
        },

        "config":                       config,     # construct_config

        "intake": {
            "sent_type":                intake.get('sent_type'),
            "sent_id":                  intake.get('sent_id'),
            "sent_mods":                str(intake.get('sent_mods')),
            "map_full":                 str(intake.get('map_full')),
            "temp_rank":                int(intake.get('temp_rank'))
        }        
    }

def construct_active(match_id: int):    

    return {
        "match_id":     match_id,
        "given":        time.time()
    }

def construct_config(
    source: int = 0,
    goal: int = 0,
    time: int = 0,
    policy: int = 0,        
    mods: list = [],
    crossclient: int = 0
):    

    return {
        "source":       source,
        "goal":         goal,
        "time":         time,
        "policy":       policy,
        "mods":         mods,
        "crossclient":  crossclient
    }
