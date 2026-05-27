


import os
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ......external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from ......external.osu_api import get_beatmap, get_beatmapset
from ......actions.messages import safe_edit_query, safe_query_answer
from ......actions.context import set_message_context
from ......external.osu_and_meatconnect import download_osz_async
from ..send_audio import send_audio
from ..utils import beatmap_artists_and_audio_path

from config import OSU_SESSION, OSZ_DIR



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["muz_context", "map|pkbmap|inline", "<map_id>", "<origin_user_id>"]
    action = parts[1]
    beatmap_id = str(parts[2])
    origin_uid = int(parts[3])

    if action == "pkbmap" or action == "inline":
        delete_origin = False
    else:
        delete_origin = True
        
    # так как delete это режим для обычной music
    if delete_origin:
        if uid_click != origin_uid:
                await safe_query_answer(query, text="Не твои кнопки")
                return
    
    if not action == "inline":
        beatmap_data = await get_beatmap(beatmap_id)

        if beatmap_data:
            converted_mapset_id = (
                beatmap_data.get("beatmapset_id")
            )

            if converted_mapset_id:
                beatmap_id = converted_mapset_id

    elif action == "inline":
        # beatmap_data = await get_beatmapset(beatmap_id)

        # if beatmap_data:
            
        #     try:
        #         beatmap_id = beatmap_data['beatmaps'][0]['id']
        #     except:
        #         pass

        # ожидается мапсет id?
        pass

    
    await safe_query_answer(query, show_alert=False)
  
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return
    
    await handle_map_action(
        update,
        context,
        beatmap_id,
        send_audio,
        download_osz_async,
        beatmap_artists_and_audio_path,
        get_beatmap_title_from_file,
        get_beatmap_creator_from_file,
        set_message_context,
        OSU_SESSION,
        OSZ_DIR,
        delete_origin
    )

async def handle_map_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    beatmap_id: str,
    send_audio,
    download_osz_async,
    beatmap_artists_and_audio_path,
    get_beatmap_title_from_file,
    get_beatmap_creator_from_file,
    set_message_context,
    OSU_SESSION,
    OSZ_DIR,
    delete_origin
):
    query = update.callback_query
    origin_message = query.message

    uid_click = query.from_user.id
  
    status_msg = None

    try:
        if delete_origin:
            try:
                await origin_message.edit_text(text="`Загрузка...`", parse_mode="Markdown")
            except Exception:
                pass
        else:
            # query
            if origin_message is not None:    
                status_msg = await query.message.reply_text(text="`Загрузка...`", parse_mode="Markdown")

            # inline
            else:
                status_msg = await context.bot.send_message(
                    chat_id=update.effective_user.id, 
                    text="`Загрузка...`", 
                    parse_mode="Markdown"
                )

            

        result = await download_osz_async(
            beatmap_id,
            OSU_SESSION,
            OSZ_DIR
        )

        if not result:
            raise RuntimeError("Download failed")

        mapset_id = str(result["mapset_id"])
        base_path = result["path"]

        title, artist, audio_name, bg_path = await beatmap_artists_and_audio_path(base_path)

        audio_file_path = os.path.join(base_path, audio_name)

        bot_msg = await send_audio(
            update,
            context,
            audio_file_path,
            title,
            artist,
            bg_path,
            beatmap_id
        )

        if bot_msg:
            set_message_context(
                bot_msg,
                reply=False,
                mapset_id=int(mapset_id),
                map_title=await get_beatmap_title_from_file(mapset_id),
                mapper_username=await get_beatmap_creator_from_file(mapset_id),
                origin_call_user_id=uid_click,
            )
        if delete_origin:
            try:
                await asyncio.sleep(0.5)

                await context.bot.delete_message(
                    chat_id=origin_message.chat_id,
                    message_id=origin_message.message_id
                )
            except Exception:
                pass

    except Exception as e:
        print("handle_map_action error:", e)

    finally:
        
        if status_msg:
            try:
                await asyncio.sleep(1)
                await status_msg.delete()
            except Exception:
                pass
