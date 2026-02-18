


import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TOKEN
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
from modules.commands.fun.doubt.doubt import doubt
from modules.commands.fun.blacks.blacks import blacks
from modules.commands.fun.reminders.reminders import reminders_command
from modules.commands.fun.random_image.random_image import random_image

# service
from modules.commands.service import (
    start_help,
    set_name, settings_cmd,
    uptime, ping
)

# other callbacks
from modules.commands.service.settings.callback import callback as settings_handler
from modules.actions.osu_chat import callback as osu_chat_callback

# команды не начинающиеся со start_ не асинхронные.
def register_commands(app):
    command_map = {

        # osu
       
        # beatmaps
        ("maps_skill", "ms"):               start_maps_skill,
        ("music",):                         start_beatmap_audio,
        ("beatmaps", "b"):                  beatmaps,
        ("simulate",):                      simulate,

        # cards
        ("card", "c"):                      start_card,
        ("skills",):                        start_skills,
        ("cardtop", "ct"):                  start_card_top5,
        ("map", "cardmap", "cm"):           start_beatmap_card,

        # leaderboard
        ("leaderboard", "topchat", "l"):    start_leaderboard_chat,

        # profile
        ("pc",):                            start_compare_profile,
        ("profile", "p"):                   start_profile,
        ("average", "avg", "a"):            start_average,
        ("mappers",):                       start_mappers,
        ("mods",):                          start_mods,
        ("anime", "goon"):                  start_anime,
        
        # scores
        ("recent", "rs", "r"):              start_rs,
        ("nochoke", "n"):                   start_nochoke,
        ("recent_fix", "fix", "f"):         start_recent_fix,
        ("s", "sc", "score", "scores"):     start_scores_best,  
              
        # osu_games
        ("challenge",):                     start_challenge,
        ("higherlower", "hl"):              start_higherlower_game,
      
        # fun
        ("gn",):                            random_image,
        ("doubt", "ban"):                   doubt,
        ("blacks",):                        blacks,
        ("reminders",):                     reminders_command,

        # service
        ("start", "help"):                  start_help, 
        ("name", "link", "nick", "osu"):    set_name,
        ("settings",):                      settings_cmd,
        ("ping",):                          ping,
        ("uptime",):                        uptime
    }

    for names, handler in command_map.items():
        for name in names:
            app.add_handler(CommandHandler(name, handler))

def register_callbacks(app):
    callbacks = [
        # beatmaps
        (callback_bms,      r"^beatmaps_"),
        (callback_msk1,     r"^ms_(skill|mod|lazer|tol):"),
        (callback_msk2,     r"^ms_page:"),
        (callback_sim,      r"^simulate_"),
        (callback_sim_ctx,  r"^sim_context:(map|cancel)"),

        # cards
        (callback_map_ctx,  r"^card_beatmap_context:(map|cancel)"),

        # leaderboard
        (callback_lb,       r"^leaderboard_chat_"),

        # profile
        (callback_prf_ctx,  r"^profile_context:(username|cancel)"),
        (callback_avg,      r"^average1:(u|c)"),

        # scores
        (callback_rs,       r"^rs_"),
        (callback_scb,      r"^score_best:(map|cancel)"),
        (callback_nch,      r"^page_\d+_\d+$"),
        
        # osu_games
        (callback_day,      r"^challenge_(main|next|finish|skip|leaderboard|info)"),
        (callback_hl,       r"^osugamehl_(main|next|finish|\d+)"),

        # service
        (settings_handler,  r"^settings_"),                    
        (osu_chat_callback, r"^send_pm_with_link_to:"),        
    ]

    for handler, pattern in callbacks:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))

def setup_logging():
    class ShortNetworkHandler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if "NetworkError" in msg:
                print("NetworkError")
            else:
                print(msg)

    logger = startup()
    logger.addHandler(ShortNetworkHandler())

def main():  
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, check_message)
    )

    register_commands(app)
    register_callbacks(app)
    setup_logging()
    
    try:
        app.run_polling()
        
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
