


from telegram import Update
from telegram.ext import ContextTypes

from .messages import safe_send_message, safe_query_answer
from ..systems.auth import check_osu_verified, get_osu_id
from ..external.osu_api_chat import send_pm
from ..external.osu_api import get_beatmap, get_osu_token



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)    

    data = query.data

    if data.startswith("send_pm_with_link_to:"):   
        try:
            beatmap_id = int(data.split(":", 1)[1])
            # print(beatmap_id)

            osu_name = await check_osu_verified(user_id)
            if not osu_name:
                await safe_query_answer(query, "⚠ Не сохранен ник, это делается командой /name")
                return            
            
            osu_id = await get_osu_id(user_id)
            if osu_id: 
                osu_id = str(osu_id) 
            else: 
                return               
            
            await safe_query_answer(query,"🍉 Отправляется сообщение в осу...")  

            token = await get_osu_token()
            map = await get_beatmap(beatmap_id, token)
            

            text = "["

            text += f"http://osu.ppy.sh/b/{str(beatmap_id)} " 
            
            text += f"{map['beatmapset']['artist']}  -  "
            text += f"{map['beatmapset']['title']}  "  
            text += f"[{map['version']}]"          
                   
            text += "]     "
            
            # text += f"mapper: {map['beatmapset']['creator']} | "
            # text += f"status: {(str(map['status'])).upper()} | "                        
            # text += f"stars: {round(map['difficulty_rating'], 2)}★"

            # text += f"     [https://t.me/fujiyaosu [help]] | [https://t.me/fujiyaosu [help]] "

            osu_id = "26197609"
            await send_pm(osu_id, text, action = False)

        except Exception as e:             
            print(e)   
            try:
                await safe_query_answer(query,f"🐟 Подзравляю, это неизвестная ошибка! \n\nЕсли она повторяется, отправь ее пожалуйста мне (@fujiya_sama) или в чат группы (@fujiyaosu) \n\nОшибка: {e}")
            except Exception as e: print(e)          
