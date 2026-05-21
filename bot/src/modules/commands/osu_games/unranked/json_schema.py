


import time



def construct_user(
    osu_id: int,
    osu_name: str,
    tg_id: int,
    tg_name: str,
    points: dict = None,
    config: dict = None,
    intake: dict = None,
    active_matches: list[str] | None = None,
    meta: dict = None,
):  
    if points is None: points = {}
    if config is None: config = construct_config()
    if intake is None: intake = {
        "sent_type":                "map",
        "sent_id":                  "929464",
        "sent_mods":                "NM",
        "map_full":                 "Карта не выбрана, может прочитать помощь?",
        "map_id":                   "929464",
        "temp_rank":                "0",
        "DA_values":                None
    },
    if active_matches is None:
        active_matches = []    
    if meta is None: meta = construct_meta()

    return {
        "osu":{
            "username":     str(osu_name),
            "id":           int(osu_id)
        },
        
        "telegram":{
            "username":     str(tg_name),                    
            "id":           int(tg_id),
        },

        "points": {
            "current":              points.get("current", 1000),
            "min":                  points.get("min", 1000),
            "max":                  points.get("max", 1000)
        },        

        "intake": {
            "sent_type":                intake.get('sent_type'),
            "sent_id":                  intake.get('sent_id'),
            "sent_mods":                str(intake.get('sent_mods')),
            "map_full":                 str(intake.get('map_full')),
            "map_id":                   str(intake.get('map_id')),
            "temp_rank":                str(intake.get('temp_rank'))
        },

        "meta":                         meta,
        "active_matches":               active_matches,
        "config":                       config,
    }

def construct_meta(
    skip_tutorial: bool = False,
    hide_help: bool = False
):

    return {
        "skip_tutorial": skip_tutorial,
        "hide_help": hide_help
    }

def construct_config(
    source: int = 0,
    goal: int = 0,
    time: int = 0,
    mods: list | None = None,
    crossclient: int = 0
):    
    if mods is None:
        mods = []

    return {
        "source":       source,
        "goal":         goal,
        "time":         time,
        "mods":         mods,
        "crossclient":  crossclient
    }

def construct_match(
    creator: dict,
    config: dict,
    intake: dict,
    member: dict | None = None
):
    timestamp = int(time.time())

    match_id = f"{creator['osu']['id']}{timestamp}"

    return match_id, {
        "id": match_id,

        "track": True,
        "created_at": timestamp,
        "started_at": None,

        "submit_state": {                                             
            "creator": False,
            "member": False,
        },
        "submit_result": {                                             
            "creator": 0.0, 
            "member": 0.0
        },

        "state": {
            "started": False,
            "finished": False,
            "winner": None,
            "elo_calculated": False
        },

        "config": config,

        "intake": intake,

        "creator": {
            "osu_id": creator["osu"]["id"],
            "osu_name": creator["osu"]["username"],

            "tg_id": creator["telegram"]["id"],
            "tg_name": creator["telegram"]["username"]
        },

        "member": member
    }