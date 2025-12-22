


import logging

from telegram.error import NetworkError
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.ext import MessageHandler, filters, CallbackQueryHandler

from modules.systems.startup import startup

from modules.commands.every_message.check_message import check_message

from modules.commands.osu.rs.rs import start_rs
from modules.commands.osu.name.name import set_name
from modules.commands.osu.mods.mods import start_mods
from modules.commands.osu.simulate.simulate import simulate
from modules.commands.osu.beatmaps.beatmaps import beatmaps
from modules.commands.osu.card_profile.card import start_card
from modules.commands.osu.profile.profile import start_profile
from modules.commands.osu.challenge.challenge import challenge
from modules.commands.osu.mappers.mappers import start_mappers
from modules.commands.osu.nochoke.no_choke import start_nochoke
from modules.commands.osu.maps_skill.maps_skill import start_farm
from modules.commands.osu.average.average import start_average_stats
from modules.commands.osu.recent_fix.recent_fix import start_recent_fix
from modules.commands.osu.music.beatmap_audio import start_beatmap_audio
from modules.commands.osu.compare_profile.compare_profile import start_compare_profile

from modules.commands.fun.doubt.doubt import doubt
from modules.commands.fun.blacks.blacks import blacks
from modules.commands.fun.random_image.random_image import random_image

from modules.commands.sevice.ping.ping import ping
from modules.commands.sevice.uptime.uptime import uptime
from modules.commands.sevice.help.help import start_help
from modules.commands.sevice.settings.settings  import settings_cmd
from modules.commands.sevice.forum_db_related.getthreads import dev_getthreads

from .config import TOKEN



def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))
    
    #async
    app.add_handler(CommandHandler("mods", start_mods))
    app.add_handler(CommandHandler("mappers", start_mappers))

    app.add_handler(CommandHandler("profile", start_profile))
    app.add_handler(CommandHandler("p", start_profile))

    app.add_handler(CommandHandler("card", start_card))  
    app.add_handler(CommandHandler("c", start_card))  

    app.add_handler(CommandHandler("recent_fix", start_recent_fix))
    app.add_handler(CommandHandler("fix", start_recent_fix))
    app.add_handler(CommandHandler("f", start_recent_fix))   
    
    app.add_handler(CommandHandler("recent", start_rs))
    app.add_handler(CommandHandler("rs", start_rs))    
    app.add_handler(CommandHandler("r", start_rs))

    app.add_handler(CommandHandler("pc", start_compare_profile))    
 
    app.add_handler(CommandHandler("start", start_help))
    app.add_handler(CommandHandler("help", start_help))
      
    app.add_handler(CommandHandler("music", start_beatmap_audio))

    app.add_handler(CommandHandler("maps_skill", start_farm))
    app.add_handler(CommandHandler("ms", start_farm))
    
    app.add_handler(CommandHandler("average", start_average_stats))
    app.add_handler(CommandHandler("avg", start_average_stats))
    app.add_handler(CommandHandler("a", start_average_stats))

    app.add_handler(CommandHandler("nochoke", start_nochoke))
    app.add_handler(CommandHandler("n", start_nochoke))

    #TODO make async
    app.add_handler(CommandHandler("simulate", simulate))
    app.add_handler(CommandHandler("s", simulate))

    app.add_handler(CommandHandler("settings", settings_cmd))  

    app.add_handler(CommandHandler("beatmaps", beatmaps))
    app.add_handler(CommandHandler("b", beatmaps))

    app.add_handler(CommandHandler("name", set_name))
    app.add_handler(CommandHandler("link", set_name))
    app.add_handler(CommandHandler("nick", set_name))
    app.add_handler(CommandHandler("osu", set_name))

    app.add_handler(CommandHandler("gn", random_image))    

    app.add_handler(CommandHandler("doubt", doubt))
    app.add_handler(CommandHandler("blacks", blacks))

    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("getthreads", dev_getthreads))

    app.add_handler(CommandHandler("challenge", challenge))


    app.add_handler(CallbackQueryHandler(rs_button, pattern=r"^rs_"))
    app.add_handler(CallbackQueryHandler(button_handler_profile, pattern=r"^(profile|card|noop)$"))
    app.add_handler(CallbackQueryHandler(beatmaps_button_handler, pattern="^beatmaps_"))    
    app.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^settings_"))
    # app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(next_challenge|finish_challenge|leaderboard|info|skip_challenge|menu_challenge)$"))
    app.add_handler(CallbackQueryHandler(simulate_button_handler, pattern="^simulate_"))

    app.add_handler(CallbackQueryHandler(farm_pagination_callback, pattern=r"^farm_page:"))
    app.add_handler(CallbackQueryHandler(farm_step_callback, pattern=r"^farm_(skill|mod|lazer|tol):"))
    app.add_handler(CallbackQueryHandler(page_callback_choke, pattern=r"^page_\d+_\d+$"))
    
    app.add_handler(CommandHandler("reminders", reminders_command))

    class ShortNetworkHandler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if "NetworkError" in msg: print("NetworkError")
            else: print(msg)

    logger = startup()
    logger.addHandler(ShortNetworkHandler())    

    try: app.run_polling()
    except NetworkError:  print("NetworkError")
if __name__ == "__main__":
    main()