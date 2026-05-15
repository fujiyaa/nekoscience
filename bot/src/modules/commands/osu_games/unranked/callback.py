


import traceback
from telegram import Update, LinkPreviewOptions, MessageEntity
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from .actions.finish import finish_game
from .actions.create import next_game
from ....systems.json_files import load_score_file
from .buttons import get_keyboard
from ....external.localapi import read_file_neko, insert_to_file_neko
from ....systems.auth import get_osu_id
from .json_schema import construct_user, construct_match
from .options import *
from .match import *
from .rank import *

from config import SUPPORT_STUB, MAX_TEXT_LENGTH
from longtext import UNRANKED_HELP, UNRANKED_HELP_LINKS, UNRANKED_HELP_ELO 
from longtext import UNRANKED_HELP_END, UNRANKED_HELP_TIME, UNRANKED_HELP_MAIN


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    try:
        payload = data.removeprefix("unranked_")

        if ":" in payload:
            main_part, owner_id_str = payload.rsplit(":", 1)
            owner_id = int(owner_id_str)
        else:
            main_part = payload
            owner_id = None

        parts = main_part.split("_")
        action = parts[0]
        subaction = parts[1]
        
        if action == "round" and subaction == "join":
            if owner_id == query.from_user.id:
                await query.answer("⚠️ Нельзя играть самому с собой, пригласи кого-нибудь или отмени раунд.", show_alert=True)
            else:
                await query.answer("☑️ Начинаем...", show_alert=True)            

        if owner_id is not None and query.from_user.id != owner_id:  
            await query.answer("❔ Чужие кнопки", show_alert=True)
            return
        
        osu_id = await get_osu_id(str(owner_id))
        if osu_id: 
            osu_id = str(osu_id) 
        else: 
            return    
        
        response = await read_file_neko(d_file)
        data = response.get("current", {})

        user = data[osu_id]

        config = user.get("config")
        intake = user.get("intake")
        points = user.get("points")
        active_matches = user.get("active_matches")
        current = points.get("current")
        rank = intake.get("temp_rank")

        osu, tg = user.get("osu"), user.get("telegram")     
        osu_name, osu_id = osu.get("username"), osu.get("id")
        tg_name, tg_id = tg.get("username"), tg.get("id")

        map_full = intake['map_full']
        
        if intake["sent_type"] == 'score':
            try:
                cached_entry =  load_score_file(intake['sent_id'])                          

                map_id = cached_entry.get('map').get('beatmap_id')
                
                sent_client_lazer = bool(cached_entry.get('state').get('lazer'))

                sent_options = [
                    int(((cached_entry.get('lazer_data') or {}).get('total_score')) or 0),
                    int(((cached_entry.get('osu_score') or {}).get('score_legacy')) or 0),                    
                    float(((cached_entry.get('osu_score') or {}).get('accuracy')) or 0)*100,
                    int(((cached_entry.get('osu_score') or {}).get('count_miss')) or 0),
                    int(((cached_entry.get('osu_score') or {}).get('max_combo')) or 0)
                ]

                choice_text = f"<b>Условие победы:</b> {GOAL_OPTIONS[config.get('goal')]}: "
                choice_data = sent_options[config.get('goal')]
                            
                url_config = "https://osu.ppy.sh/scores/"            
                    
            except Exception:
                traceback.print_exc()
                await query.answer("❌ Ошибка", show_alert=True)
                return
        else:
            try:
                map_id = intake['sent_id']

                choice_text = f"<b>Условие победы:</b> {GOAL_OPTIONS[config.get('goal')]}"
                choice_data = ""

                url_config = "https://osu.ppy.sh/b/"

            except Exception:
                traceback.print_exc()
                await query.answer("❌ Ошибка", show_alert=True)
                return

        creation_text = f"<b>Создание раунда</b>"
        rating_text = f"<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})"
        difficulty_text = f'<a href="https://osu.ppy.sh/b/{map_id}">{map_full} 🔗</a>'

        text = f"{rating_text}\n\n{creation_text}: {difficulty_text}\n\n{choice_text}{choice_data}"

        link_preview = LinkPreviewOptions(
            url=BANNER_OPTIONS[0],
            is_disabled=False,
            prefer_small_media=False,
            prefer_large_media=True,
            show_above_text=True
        )
        
        if action == "menu":
            if subaction == "main":
                reply_markup = get_keyboard(
                    "main-menu", 
                    config, 
                    owner_id=tg_id
                )

                await query.edit_message_text(
                    text = MAIN_MENU_TEXT,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "aboutcreation":
                reply_markup = get_keyboard(
                        "main-help",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    UNRANKED_HELP_LINKS,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "aboutelo":
                reply_markup = get_keyboard(
                        "main-help",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    UNRANKED_HELP_ELO,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "aboutend":
                reply_markup = get_keyboard(
                        "main-help",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    UNRANKED_HELP_END,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "abouttime":
                reply_markup = get_keyboard(
                        "main-help",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    UNRANKED_HELP_TIME,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "aboutgame":
                reply_markup = get_keyboard(
                        "main-help",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    UNRANKED_HELP_MAIN,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "helpnested":
                reply_markup = get_keyboard(
                        "main-helpnested",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    "<b>Выбери раздел.</b>",
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview
                )

            elif subaction == "allactive":

                response = await read_file_neko(m_file)

                matches = response.get("current", {})

                matches_list = get_all_matches(matches)

                text = "\n".join(matches_list)

                def tg_len(text: str) -> int:
                    return len(text.encode("utf-16-le")) // 2
                
                entities = [
                    MessageEntity(
                        type="expandable_blockquote",
                        offset=0,                     
                        length=tg_len(text)    
                    )
                ]

                reply_markup = get_keyboard(
                        "main-back",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    f"{text}\n\nЗдесь отображаются все активные раунды.\nНажми на блок, чтобы развернуть текст",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    entities=entities
                )

            elif subaction == "myactive":

                response = await read_file_neko(m_file)

                matches = response.get("current", {})

                matches_list = get_user_matches(
                    matches,
                    active_matches
                )

                text = "\n".join(matches_list)

                def tg_len(text: str) -> int:
                    return len(text.encode("utf-16-le")) // 2
                
                entities = [
                    MessageEntity(
                        type="expandable_blockquote",
                        offset=0,                     
                        length=tg_len(text)    
                    )
                ]

                reply_markup = get_keyboard(
                        "main-back",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    f"{text}\n\nЗдесь отображаются твои активные раунды.\nНажми на блок, чтобы развернуть текст",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    entities=entities
                )

            elif subaction == "mystats":
                rank = get_player_rank(data, osu_id)
                rating_text = f"<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})"
                text = f"""
{rating_text}

<b>ELO:</b>
- минимум: {points.get('min')}
- максимум: {points.get('max')}

<b>Активных раундов:</b> {len(active_matches)} (см.⏳ Мои игры)

<i>больше статистики тут, если режим станет популярным</i>
"""               

                reply_markup = get_keyboard(
                        "main-back",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    parse_mode="HTML"
                )

            elif subaction == "alltop":
                
                response = await read_file_neko(d_file)

                users = response.get("current", {})

                ranking = get_top_players(users, limit=50)

                text = "\n".join(ranking)

                def tg_len(text: str) -> int:
                    return len(text.encode("utf-16-le")) // 2

                entities = [
                    MessageEntity(
                        type="expandable_blockquote",
                        offset=0,
                        length=tg_len(text)
                    )
                ]

                reply_markup = get_keyboard(
                    "main-back",
                    owner_id=owner_id
                )

                await query.edit_message_text(
                    f"{text}\n\n🏆 Топ-50 ELO.",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    entities=entities
                )

            return    

        if len(active_matches) < 10:                   
            if action == "switch":
                if subaction == "mods":
                    if config.get('source') == 0:

                        await query.answer("Этот параметр не учитывается, если выбрано: \n\n⤴️ Против скора - в этом режиме моды будут выбраны из твоей игры\n\nЧтобы изменить моды, выбери другой режим в первом пункте меню!", show_alert=True)

                    else:
                        reply_markup = get_keyboard(
                            "mods",
                            config,
                            intake,
                            owner_id=owner_id
                        )

                        await query.edit_message_text(
                            """ 
✖️ Не выбирай несовместимые моды, иначе не сможешь сабмитнуть скор.

➕ Выбери FM (любые моды, в т.ч. лазера), если хочешь дать фору""",
                            reply_markup=reply_markup,
                            link_preview_options=link_preview
                        )

                    return

                if subaction == "source":
                    if intake.get('sent_type') == 'score':
                        await switch_config(config, subaction, SOURCE_OPTIONS)
                    else: 
                        config['source'] = 1
                        await query.answer("""
Сейчас выбрана карта как источник.
                                           
Чтобы не играть заново, в команду нужно присылать скор:

✅ /unranked https://osu.ppy.sh/SCORES/...
""", show_alert=True)

                elif subaction == "time":
                    await switch_config(config, subaction, TIME_OPTIONS)
                elif subaction == "goal":
                    await switch_config(config, subaction, GOAL_OPTIONS)
                elif subaction == "policy":
                    await switch_config(config, subaction, POLICY_OPTIONS)
                elif subaction == "crossclient":                    
                    blocked = set()
                    if intake["sent_type"] == 'score':
                        if sent_client_lazer:
                            blocked.add(1)
                        else: 
                            blocked.add(2)
                    await switch_config(config, subaction, CROSSCLIENT_OPTIONS, blocked)
                else: return

                data[osu_id] = construct_user(
                    osu_id, 
                    osu_name, 
                    tg_id,
                    tg_name,
                    points=points,
                    config=config,
                    intake=intake,                
                    active_matches=active_matches,
                )
                await insert_to_file_neko(d_file, data)

                print("config updated")
                
                reply_markup = get_keyboard("main", config, intake, owner_id=owner_id)

                try:
                    if intake['sent_type'] == 'score':
                        choice_text = f"{GOAL_OPTIONS[config.get('goal')]}: "
                        choice_data = sent_options[config.get('goal')]
                    else:
                        choice_text = f"<b>Условие победы:</b> {GOAL_OPTIONS[config.get('goal')]}" 
                        choice_data = ""

                    if config.get('source') == 1:
                        choice_text = f"<b>Условие победы:</b> {GOAL_OPTIONS[config.get('goal')]}" 
                        choice_data = ""

                    text = f"{rating_text}\n\n{creation_text}: {difficulty_text}\n\n{choice_text}{choice_data}"

                    await query.edit_message_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        link_preview_options=link_preview
                    )
                except Exception:
                    await safe_query_answer(query, show_alert=False)

            elif action == "modtoggle":
                if subaction == "back":
                    reply_markup = get_keyboard(
                        "main",
                        config,
                        intake,
                        owner_id=owner_id
                    )

                    await query.edit_message_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        link_preview_options=link_preview
                    )
                    return
                
                if config.get('source') == 0:

                    await query.answer("Этот параметр не учитывается, если выбрано: \n\n⤴️ Против скора - в этом режиме моды будут выбраны из твоей игры\n\nЧтобы изменить моды, выбери другой режим в первом пункте меню!", show_alert=True)

                else:

                    mod = subaction

                    mods = config.get("mods", [])

                    if mod in mods:
                        mods.remove(mod)
                    else:
                        mods.append(mod)

                    config["mods"] = mods

                    data[osu_id] = construct_user(
                        osu_id, 
                        osu_name, 
                        tg_id,
                        tg_name,
                        points=points,
                        config=config,
                        intake=intake,                
                        active_matches=active_matches,
                    )

                    await insert_to_file_neko(d_file, data)

                    reply_markup = get_keyboard(
                        "mods",
                        config,
                        intake,
                        owner_id=owner_id
                    )

                    await query.edit_message_reply_markup(
                        reply_markup=reply_markup
                    )
                
                return
            
            elif action == "round":  
                if subaction == "create":

                    response = await read_file_neko(m_file)

                    matches = response.get("current", {})

                    match_id, match_data = construct_match(
                        creator=user,
                        config=config,
                        intake=intake
                    )

                    matches[match_id] = match_data

                    await insert_to_file_neko(m_file, matches)


                    if match_id not in active_matches:
                        active_matches.append(match_id)

                    data[osu_id] = construct_user(
                        osu_id,
                        osu_name,
                        tg_id,
                        tg_name,
                        points=points,
                        config=config,
                        intake=intake,
                        active_matches=active_matches
                    )

                    await insert_to_file_neko(d_file, data)


                    reply_markup = get_keyboard(
                        "round-configured",
                        config,
                        intake,
                        owner_id=owner_id
                    )

                    if config.get('policy') == 1:
                        policy_text = "Создатель этого раунда будет подтверждать, что хочет играть."
                    else:
                        policy_text = "Играть можно сразу после кнопки участвовать."

                    if config.get('crossclient') == 2:
                        crossclient_text = "только Lazer"
                    elif config.get('crossclient') == 1:
                        crossclient_text = "только Stable"
                    else:
                        crossclient_text = "любой"

                    some_mods = config.get("mods", [])
                    mods_text = "".join(some_mods) if some_mods else "нет"

                    goal_text = GOAL_OPTIONS[config.get('goal')]
                    time_text = TIME_OPTIONS[config.get('time')]


                    text = f"""
Новый раунд создан! {policy_text}

<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})

<b>Условие победы:</b> {goal_text}
<b>Клиент:</b> {crossclient_text}, {time_text}

<b>Моды:</b> {mods_text},
<b>Карта:</b> <a href="https://osu.ppy.sh/b/{map_id}">{map_full} 🔗</a>
"""
                    
                elif subaction == "donotcreate":
                    reply_markup = None
                    text = "💤 Раунд отменен его создаталем."

                else: return

                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    parse_mode="HTML"
                )                

            elif action == "help":
                if subaction == "back":
                    reply_markup = get_keyboard(
                        "main",
                        config,                        
                        intake,
                        owner_id=owner_id
                    )

                    await query.edit_message_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        link_preview_options=link_preview
                    )
                else:
                    reply_markup = get_keyboard(
                        "help",
                        config,
                        intake,
                        owner_id=owner_id
                    )

                    await query.edit_message_text(
                        UNRANKED_HELP,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        link_preview_options=link_preview
                    )
                return
            else:
                print("else")
        else:
            await query.answer("⭐️ Нельзя изменить настройку во время активного раунда", show_alert=True)
            return

        # actions = {
        #     "next": next_game,
        #     "finish": finish_game,
        #     "main": higherlower_game
        # }

        # if action in actions:
        #     if arg is not None:
        #         await actions[action](update, context, arg)
        #     else:
        #         await actions[action](update, context)
        # else:
        #     await query.edit_message_text("Неизвестная кнопка!")

        # await safe_query_answer(query, show_alert=False)

    except Exception:
        error_details = traceback.format_exc()
        full_text = f"{error_details}\n\n{SUPPORT_STUB}"

        sended = await safe_query_answer(query, text=full_text, show_alert=True)
        if sended:
            return

        try:
            for i in range(0, len(full_text), MAX_TEXT_LENGTH):
                chunk = full_text[i:i + MAX_TEXT_LENGTH]
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=chunk
                )
        except Exception as e:
            print(e)

async def switch_config(config, key: str, options: list, blocked: set[int] | None = None):
    blocked = blocked or set()

    current = config.get(key, 0)

    n = len(options)
    for step in range(1, n + 1):
        nxt = (current + step) % n
        if nxt not in blocked:
            config[key] = nxt
            return

    config[key] = current