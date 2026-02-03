


import logging

from telegram.error import NetworkError
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
from modules.commands.osu.rs.rs import start_rs
from modules.commands.osu.name.name import set_name
from modules.commands.osu.mods.mods import start_mods
from modules.commands.osu.simulate.simulate import simulate
from modules.commands.osu.beatmaps.beatmaps import beatmaps
from modules.commands.osu.card_profile.card import start_card
from modules.commands.osu.card_skills.card import start_skills
from modules.commands.osu.profile.profile import start_profile
from modules.commands.osu.mappers.mappers import start_mappers
from modules.commands.osu.nochoke.no_choke import start_nochoke
from modules.commands.osu.maps_skill.maps_skill import start_maps_skill
from modules.commands.osu.check_for_anime.anime import start_anime
from modules.commands.osu.average.average import start_average_stats
from modules.commands.osu.recent_fix.recent_fix import start_recent_fix
from modules.commands.osu.music.beatmap_audio import start_beatmap_audio
from modules.commands.osu.daily_challenge.v1.challenge import start_challenge
from modules.commands.osu.compare_profile.compare_profile import start_compare_profile
from modules.commands.osu.card_top5.card import start_card as start_card_top5
from modules.commands.osu.leaderboard_chat.leaderboard import start_leaderboard_chat
from modules.commands.osu.scores_best.scores_best import start_scores_best
from modules.commands.osu.card_beatmap.beatmap import start_beatmap_card

# fun
from modules.commands.fun.doubt.doubt import doubt
from modules.commands.fun.blacks.blacks import blacks
from modules.commands.fun.reminders.reminders import reminders_command
from modules.commands.fun.random_image.random_image import random_image

# service
from modules.commands.service.ping.ping import ping
from modules.commands.service.uptime.uptime import uptime
from modules.commands.service.help.help import start_help
from modules.commands.service.settings.settings import settings_cmd
from modules.commands.osu.scoreoverride.score import score as scoreoverride
# from modules.commands.service.forum_db_related.getthreads import dev_getthreads

# callback
from modules.commands.osu.rs.callback import callback as rs_handler
from modules.commands.osu.nochoke.callback import callback as nochoke_handler
from modules.commands.osu.beatmaps.callback import callback as beatmaps_handler
from modules.commands.osu.simulate.callback import callback as simulate_handler
from modules.commands.osu.daily_challenge.v1.callback import callback as challenge_callback
from modules.commands.osu.maps_skill.callback_level1 import ms_step_callback as ms_callback1
from modules.commands.osu.maps_skill.callback_level2 import ms_pagination_callback as ms_callback2
from modules.commands.osu.leaderboard_chat.callback import callback as leaderboard_callback
from modules.commands.osu.scores_best.callback import callback as scores_best_callback
from modules.commands.osu.profile.callback import callback as profile_ctx_callback
from modules.commands.osu.simulate.context.callback import callback as simulate_ctx_callback
from modules.commands.osu.card_beatmap.context.callback import callback as card_map_ctx_callback


from modules.commands.service.settings.callback import callback as settings_handler

from modules.actions.osu_chat import callback as osu_chat_callback



# команды не начинающиеся со start_ не асинхронные.
def register_commands(app):
    command_map = {
        # osu
        ("mods",):                          start_mods,
        ("mappers",):                       start_mappers,
        ("profile", "p"):                   start_profile,
        ("card", "c"):                      start_card,
        ("map", "cardmap", "cm"):           start_beatmap_card,
        ("skills",):                        start_skills,
        ("cardtop", "ct"):                  start_card_top5,
        ("recent_fix", "fix", "f"):         start_recent_fix,
        ("recent", "rs", "r"):              start_rs,
        ("pc",):                            start_compare_profile,
        ("music",):                         start_beatmap_audio,
        ("maps_skill", "ms"):               start_maps_skill,
        ("average", "avg", "a"):            start_average_stats,
        ("nochoke", "n"):                   start_nochoke,
        ("anime", "goon"):                  start_anime,
        ("challenge",):                     start_challenge,
        ("leaderboard", "topchat", "l"):    start_leaderboard_chat,
        ("s", "sc", "score", "scores"):     start_scores_best,        
        ("simulate",):                      simulate,
        ("beatmaps", "b"):                  beatmaps,
        ("name", "link", "nick", "osu"):    set_name,

        # fun
        ("gn",):                            random_image,
        ("doubt", "ban"):                   doubt,
        ("blacks",):                        blacks,
        ("reminders",):                     reminders_command,

        # service
        ("start", "help"):                  start_help,
        ("settings",):                      settings_cmd,
        ("ping",):                          ping,
        ("uptime",):                        uptime,
        ("scoreoverride",):                 scoreoverride
    }

    for names, handler in command_map.items():
        for name in names:
            app.add_handler(CommandHandler(name, handler))

def register_callbacks(app):
    callbacks = [
        (rs_handler,            r"^rs_"),
        (beatmaps_handler,      r"^beatmaps_"),
        (settings_handler,      r"^settings_"),
        (simulate_handler,      r"^simulate_"),
        (ms_callback2,          r"^ms_page:"),
        (ms_callback1,          r"^ms_(skill|mod|lazer|tol):"),
        (nochoke_handler,       r"^page_\d+_\d+$"),        
        (challenge_callback,    r"^challenge_(main|next|finish|skip|leaderboard|info)"),
        (osu_chat_callback,     r"^send_pm_with_link_to:"),
        (leaderboard_callback,  r"^leaderboard_chat_"),
        (scores_best_callback,  r"^score_best:(map|cancel)"),
        (profile_ctx_callback,  r"^profile_context:(username|cancel)"),
        (simulate_ctx_callback, r"^sim_context:(map|cancel)"),
        (card_map_ctx_callback, r"^card_beatmap_context:(map|cancel)"),
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
