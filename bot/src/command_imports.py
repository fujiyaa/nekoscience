


from modules.systems.startup import startup
from modules.commands.every_message.check_message import check_message

# osu
from modules.commands.osu import (

    # beatmaps
    start_maps_skill, start_beatmap_audio,
    beatmaps, simulate,    
    callback_bms,
    callback_msk1, callback_msk2,
    callback_sim, callback_sim_ctx, 

    # cards
    start_card, start_skills, start_card_top5, start_beatmap_card,
    callback_map_ctx,

    # leaderboard
    start_leaderboard_chat,
    callback_lb,

    # profile
    start_compare_profile, start_profile, start_average,
    start_mappers, start_mods, start_anime,
    callback_avg, callback_prf_ctx,

    # scores
    start_rs, start_nochoke, start_recent_fix, start_scores_best,
    callback_rs, callback_scb, callback_nch
)

# osu_games
from modules.commands.osu_games import (    
    start_challenge, start_higherlower_game,

    callback_day, callback_hl
)

# fun
from modules.commands.fun import (
    doubt, blacks, 
    reminders_command, 
    random_image, roll
)

# service
from modules.commands.service import (
    start_help,
    set_name, settings_cmd,
    uptime, ping
)

# inline
from modules.inline import (
    inline_osu_search
)

# other callbacks
from modules.commands.service.settings.callback import callback as settings_handler
from modules.actions.osu_chat import callback as osu_chat_callback
# from modules.inline import callback as settings_handler
