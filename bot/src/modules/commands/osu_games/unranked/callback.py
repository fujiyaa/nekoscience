


from contextlib import asynccontextmanager
import traceback
from telegram import Update, LinkPreviewOptions, MessageEntity
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from .actions.finish import finish_game
from .actions.create import next_game
from ....systems.json_files import load_score_file
from .buttons import *
from ....external.localapi import read_file_neko, insert_to_file_neko, remove_from_file_neko
from ....systems.auth import get_osu_id
from .json_schema import construct_user, construct_match
from .options import *
from .match import *
from .rank import *
from .locks import GLOBAL_LOCK

from config import SUPPORT_STUB, MAX_TEXT_LENGTH
from longtext import UNRANKED_HELP, UNRANKED_HELP_LINKS, UNRANKED_HELP_ELO 
from longtext import UNRANKED_HELP_END, UNRANKED_HELP_TIME, UNRANKED_HELP_MAIN



@asynccontextmanager
async def transaction():
    async with GLOBAL_LOCK:
        yield

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
            deleted_text = "💤 Когда-то здесь было приглашение на игру"
            async with transaction():
                try:
                    match_id = owner_id_str

                    response = await read_file_neko(m_file)
                    matches = response.get("current", {})

                    match = matches.get(match_id)
                    short_id = match_id[-5:]

                    if not match:
                        await query.answer("❌ Раунд уже удален.", show_alert=True)
                        await query.edit_message_text(
                            text=deleted_text,
                            link_preview_options=None,
                            reply_markup=None
                        )
                        return

                    creator = match.get("creator", {})

                    if creator.get("tg_id") == query.from_user.id:
                        await query.answer("❌ Нельзя играть самому с собой.", show_alert=True)
                        return

                    state = match.get("state", {})

                    if state.get("finished"):
                        await query.answer("❌ Раунд уже завершен.", show_alert=True)
                        await query.edit_message_text(
                            reply_markup=None
                        )
                        return

                    # если уже есть участник
                    if match.get("member") is not None:
                        await query.answer("❌ Раунд уже занят.", show_alert=True)
                        await query.edit_message_text(
                            reply_markup=None
                        )
                        return

                    # ❗ теперь список заявок
                    pending_joins = match.get("pending_joins") or []

                    join_osu_id = await get_osu_id(str(query.from_user.id))

                    if not join_osu_id:
                        await query.answer("❌ Осу аккаунт не авторизован? Он нужен для игры: /name", show_alert=True)
                        return

                    join_osu_id = str(join_osu_id)

                    response = await read_file_neko(d_file)
                    users = response.get("current", {})

                    join_user = users.get(join_osu_id)

                    if not join_user:
                        await query.answer("❌ Сначала посети главное меню /unranked", show_alert=True)
                        return

                    join_osu = join_user.get("osu", {})
                    join_tg = join_user.get("telegram", {})

                    # ❗ защита от дубля заявки
                    already_requested = any(
                        p.get("tg_id") == join_tg.get("id")
                        for p in pending_joins
                    )

                    if already_requested:
                        await query.answer("❌ Ты уже отправлял сюда заявку", show_alert=True)
                        return

                    owner_id = creator.get("tg_id")

                    if owner_id:
                        _id = join_osu.get('id')
                        _name = join_osu.get("username")
                        link = f'<a href="https://osu.ppy.sh/b/{_id}">{_name} 🔗</a>'
                        

                        text = (
                            f"@{creator.get('tg_name')}, запрос присоединиться\n"
                            f"<code>- ID этого раунда: {short_id}</code>\n\n"
                            f"<b>{link}</b> хочет играть!"
                        )

                        reply_markup = get_pending_join_keyboard(
                            str(match_id),
                            str(join_tg.get('id')), 
                            str(owner_id)
                        )
                        
                        try:
                            await query.message.reply_text(
                                reply_to_message_id=query.message.message_id,
                                text = text,
                                parse_mode="HTML",
                                reply_markup=reply_markup
                            ) 
                        except:
                            print('fallback')
                            await context.bot.send_message(                                                
                                chat_id=query.message.chat.id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode="HTML"
                            )
                            
                        await query.answer("📩 Заявка отправлена создателю.", show_alert=True)
                    
                    else: 
                        raise ValueError
                    
                    pending_joins.append({
                        "osu_id": join_osu.get("id"),
                        "osu_name": join_osu.get("username"),
                        "tg_id": join_tg.get("id"),
                        "tg_name": join_tg.get("username")
                    })

                    match["pending_joins"] = pending_joins
                    matches[match_id] = match

                    await insert_to_file_neko(m_file, matches)

                    print(f"added pending join for match {match_id} from user {join_osu.get('id')}")

                except:
                    await query.answer("⚠️ При доставке заявки возникли проблемы.", show_alert=True)               

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

                choice_text = f"<b>Противник должен побить:</b> {GOAL_OPTIONS[config.get('goal')]}: "
                choice_data = sent_options[config.get('goal')]

            except Exception:
                traceback.print_exc()
                await query.answer("❌ Ошибка", show_alert=True)
                return
        else:
            try:
                map_id = intake['sent_id']

                choice_text = f"<b>Условие победы:</b> {GOAL_OPTIONS[config.get('goal')]}"
                choice_data = ""

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

        if action == "matchcancel":
            try:
                async with transaction():

                    match_id = subaction

                    response = await read_file_neko(m_file)

                    matches = response.get("current", {})

                    match = matches.get(match_id)
                    short_id = match_id[-5:]

                    if not match:
                        await query.answer(
                            "Раунд уже удален.",
                            show_alert=True
                        )
                        return

                    creator = match.get("creator", {})

                    if creator.get("tg_id") != tg_id:
                        await query.answer(
                            "Можно отменять только свои раунды.",
                            show_alert=True
                        )
                        return

                    # удаление матча у участника        
                    member = match.get("member")

                    if member:
                        member_osu_id = str(member.get("osu_id"))

                        enemy_user = data.get(member_osu_id)

                        if enemy_user:
                            enemy_active = list(enemy_user.get("active_matches", []))

                            if match_id in enemy_active:
                                enemy_active.remove(match_id)

                            enemy_osu = enemy_user.get("osu", {})
                            enemy_tg = enemy_user.get("telegram", {})

                            data[member_osu_id] = construct_user(
                                member_osu_id,
                                enemy_osu.get("username"),
                                enemy_tg.get("id"),
                                enemy_tg.get("username"),
                                points=enemy_user.get("points"),
                                config=enemy_user.get("config"),
                                intake=enemy_user.get("intake"),
                                active_matches=enemy_active
                            )

                            print(f"removed match {match_id} from member {member_osu_id} (without insert to file)")
                
                    if match_id in active_matches:
                        active_matches.remove(match_id)

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

                    await insert_to_file_neko(
                        d_file,
                        data
                    )

                    print(f"removed match {match_id} from creator {creator.get('osu_id')} (insert to file)")

                    await remove_from_file_neko(
                        m_file,
                        [match_id]
                    )

                    print(f"deleted match {match_id}")

                reply_markup = get_match_edit_keyboard(
                    keyboard_type="back",
                    match_id=match_id,
                    owner_id=owner_id
                )

                text = f"""
<b>Раунд удален</b> 
<code>- ID этого раунда: {short_id}</code>
"""
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    parse_mode="HTML"
                )

                await query.answer("🗑 Создание раунда отменено.", show_alert=True)

                return
            except Exception as e:
                print(e)
                await query.answer(f"ошибка..?", show_alert=True)
                return
            
        if action == "matchedit":

            # async with transaction():

            match_id = subaction
            short_id = match_id[-5:]

            response = await read_file_neko(m_file)

            matches = response.get("current", {})

            match = matches.get(match_id)

            if not match:
                await query.answer(
                    "Раунд уже удален.",
                    show_alert=True
                )
                return
            
            creator = match.get('creator')
            member = match.get("member") or {}
            config = match.get('config')
            intake = match.get('intake')

            map_id = intake.get('map_id')
            map_full = intake.get('map_full')

            some_mods = config.get("mods", [])
            mods_text = "".join(some_mods) if some_mods else "нет"

            goal_text = GOAL_OPTIONS[config.get('goal')]
            time_text = TIME_OPTIONS[config.get('time')]
            crossclient_text = CROSSCLIENT_OPTIONS[config.get('crossclient')]

            if member:
                cancel_text = "❌ Отмена этого раунда считается поражением"
                member_str = f"\n<b>Участник:</b>  {member.get('osu_name')}"
                kb_type = "with-member"
            else:
                cancel_text = "❎ Этот раунд можно отменить без потери рейтинга"
                member_str = ""
                kb_type = "without-member"

            text = f"""
<b>Создатель:</b> {creator.get('osu_name')}{member_str}
<code>- ID этого раунда: {short_id}</code>

<b>Условие победы:</b> {goal_text}
 {crossclient_text}, {time_text}

<b>Моды:</b> {mods_text},
<b>Карта:</b> <a href="https://osu.ppy.sh/b/{map_id}">{map_full} 🔗</a>

<i>{cancel_text}</i>
"""
            reply_markup = get_match_edit_keyboard(
                kb_type,
                match_id=match_id,
                owner_id=owner_id
            )

            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                link_preview_options=link_preview,
                parse_mode="HTML"
            )
            
            return
                
        # def find_match_by_owner(matches, owner_id):
        #     for match_id, match in matches.items():
        #         creator = match.get("creator", {})
        #         if creator.get("tg_id") == owner_id:
        #             return match_id, match
        #     return None, None

        if action == "accept":
            deleted_text = "💤 Когда-то здесь была заявка на игру"
            try:
                async with transaction():                
                    target_tg_id = int(parts[1])
                    match_id = str(parts[2])
                    short_id = match_id[-5:]

                    response = await read_file_neko(m_file)
                    matches = response.get("current", {})
                    
                    match = matches.get(match_id)                    

                    if not match:
                        await query.answer(f"❌ Раунд c ID {short_id} не найден.", show_alert=True)
                        await query.edit_message_text(
                            text=deleted_text,
                            reply_markup=None
                        )
                        return

                    pending_joins = match.get("pending_joins") or []

                    pending = next(
                        (p for p in pending_joins if p.get("tg_id") == target_tg_id),
                        None
                    )

                    if not pending:
                        await query.answer(f"❌ Возможно старая заявка, ID рауда: {short_id}", show_alert=True)
                        await query.edit_message_text(
                            text=deleted_text,
                            reply_markup=None
                        )
                        return

                    match["member"] = pending
                    match["pending_joins"] = [
                        p for p in pending_joins if p.get("tg_id") != target_tg_id
                    ]

                    text = f"""
✅ @{pending.get('tg_name')}, заявка была <b>принята</b>
<code>- ID этого раунда: {short_id}</code>
<code>- инфо о раунде в меню Мои игры</code>"""                                
                
                    # запись id матча участнику            
                    response = await read_file_neko(d_file)
                    data = response.get("current", {})

                    user = data[str(pending.get('osu_id'))]

                    config = user.get("config")
                    intake = user.get("intake")
                    points = user.get("points")
                    active_matches = user.get("active_matches")
                    current = points.get("current")
                    rank = intake.get("temp_rank")

                    osu, tg = user.get("osu"), user.get("telegram")     
                    osu_name, osu_id = osu.get("username"), osu.get("id")
                    tg_name, tg_id = tg.get("username"), tg.get("id")

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

                    await insert_to_file_neko(m_file, matches)

                    print(f"added member {osu_id} to match {match_id}")

                    await insert_to_file_neko(d_file, data)

                    print(f"updated active matches for {osu_id}, added {match_id}")

                await query.edit_message_text(
                    text = text,
                    parse_mode="HTML"
                )
                
                return
            
            except Exception as e:
                print(e)
                await query.answer(f"ошибка..?", show_alert=True)
                return           

        if action == "deny":
            deleted_text = "💤 Когда-то здесь была заявка на игру"
            try:
                async with transaction():

                    target_tg_id = int(parts[1])            
                    match_id = str(parts[2])
                    short_id = match_id[-5:]

                    response = await read_file_neko(m_file)
                    matches = response.get("current", {})

                    match = matches.get(match_id)

                    if not match:
                        await query.answer(f"❌ Раунд c ID {short_id} не найден.", show_alert=True)
                        await query.edit_message_text(
                            text=deleted_text,
                            reply_markup=None
                        )
                        return

                    pending_joins = match.get("pending_joins") or []

                    pending = next(
                        (p for p in pending_joins if p.get("tg_id") == target_tg_id),
                        None
                    )

                    if not pending:
                        await query.answer(f"❌ Возможно старая заявка, ID рауда: {short_id}", show_alert=True)
                        await query.edit_message_text(
                            text=deleted_text,
                            reply_markup=None
                        )
                        return

                    match["pending_joins"] = [
                        p for p in pending_joins if p.get("tg_id") != target_tg_id
                    ]

                    matches[match_id] = match

                    await insert_to_file_neko(m_file, matches)

                    print(f"deleted pending join for match {match_id} from user {target_tg_id}")

                await query.edit_message_text(
                    text = f"💤 @{pending.get('tg_name')}, заявка была <b>отклонена</b>",
                    parse_mode="HTML",
                )
                return

            except Exception as e:
                print(e)
                await query.answer(f"ошибка..?", show_alert=True)
                return
                            
        if action == "menu":
            if subaction == "main":
                rank = get_player_rank(data, osu_id)
                rating_text = f"<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})"
                text = f"""
{rating_text}
<code>- мин/макс ELO: {points.get('min')}/{points.get('max')}</code> 
<code>- игр в процессе: {len(active_matches)}</code>

{MAIN_MENU_TEXT}
"""
                reply_markup = get_keyboard(
                        "main-menu",
                        owner_id=owner_id
                    )

                await query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    parse_mode="HTML"
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
                    f"{text}\n\nЗдесь самые новые активные раунды (вообще всех).\nНажми на блок выше, чтобы развернуть текст",
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

                reply_markup = get_active_matches_keyboard(
                    active_matches,
                    matches,
                    owner_id
                )

                if len(active_matches) < 1:
                    _text = MAIN_MENU_MYACTIVE_NONE
                elif len(active_matches) < 20:
                    _text = MAIN_MENU_MYACTIVE_SOME
                else:
                    _text = MAIN_MENU_MYACTIVE_LIMIT

                await query.edit_message_text(
                    text=f"{text}\n{_text}",
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
                    f"{text}\n\n🏆 Топ-50 ELO. Нажми на блок выше, чтобы развернуть",
                    reply_markup=reply_markup,
                    link_preview_options=link_preview,
                    entities=entities
                )

            return    

        if len(active_matches) < 20:                   
            if action == "switch":
                if subaction == "mods":
                    if config.get('source') == 0:

                        await safe_query_answer(query, "Моды нельзя изменять в режиме:\n\n ⤴️ Против скора", show_alert=True)
                            
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
                elif subaction == "crossclient":
                    blocked = set()

                    if config.get('source') == 0:             
                        if intake["sent_type"] == 'score':
                            await safe_query_answer(query, "Клиент нельзя изменять в режиме:\n\n ⤴️ Против скора", show_alert=True)
                            if sent_client_lazer:
                                config['crossclient'] = 1
                            else: 
                                config['crossclient'] = 0
                    else:
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

                async with transaction():

                    await insert_to_file_neko(d_file, data)

                    print(f"updated config for user {osu_id}")
                    
                    reply_markup = get_keyboard("main", config, intake, owner_id=owner_id)

                    try:
                        if intake['sent_type'] == 'score':
                            choice_text = f"<b>Противник должен побить:</b> {GOAL_OPTIONS[config.get('goal')]}: "
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

                    await safe_query_answer(query, "Это меню не дает никакого эффекта в режиме:\n\n ⤴️ Против скора", show_alert=True)
                            
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

                    async with transaction():
                        await insert_to_file_neko(d_file, data)

                        print(f"updated mods for user {osu_id}")

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
                    async with transaction():

                        response = await read_file_neko(m_file)

                        matches = response.get("current", {})

                        match_id, match_data = construct_match(
                            creator=user,
                            config=config,
                            intake=intake,
                        )
                        short_id = match_id[-5:]

                        matches[match_id] = match_data

                        await insert_to_file_neko(m_file, matches)

                        print(f"created match {match_id} for user {osu_id}")


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

                        print(f"updated active matches for {osu_id}, added {match_id}")


                        reply_markup = get_round_configured_keyboard(
                            match_id,
                            owner_id
                        )

                        some_mods = config.get("mods", [])
                        mods_text = "".join(some_mods) if some_mods else "нет"

                        goal_text = GOAL_OPTIONS[config.get('goal')]
                        time_text = TIME_OPTIONS[config.get('time')]
                        crossclient_text = CROSSCLIENT_OPTIONS[config.get('crossclient')]

                        text = f"""
Приглашение на игру создано!
<code>- ID этого раунда: {short_id}</code>

<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})

<b>Условие победы:</b> {goal_text}
 {crossclient_text}, {time_text}

<b>Моды:</b> {mods_text},
<b>Карта:</b> <a href="https://osu.ppy.sh/b/{map_id}">{map_full} 🔗</a>"""
                    
                elif subaction == "hide":

                    await query.edit_message_reply_markup(
                        reply_markup=None
                    )

                    return     

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
            await query.answer("⭐️ Лимит активных раундов. Удали ненужные или доиграй принятые ранее!", show_alert=True)
            return

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