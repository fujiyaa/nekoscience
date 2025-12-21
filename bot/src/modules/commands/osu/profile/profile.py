


import asyncio
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....systems.auth import check_osu_verified
from ....actions.messages import safe_send_message, safe_edit_message
from ....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from ....utils.text_format import country_code_to_flag

from .....config import COOLDOWN_STATS_COMMANDS, message_authors



async def start_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, user_request))
    
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="profile",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    MAX_ATTEMPTS = 3

    user_id = str(update.effective_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/p Fujiya` <- никнейм"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    elif update.callback_query:
        query = update.callback_query
        if query.message.text or query.message.caption:
            temp_message = await query.message.edit_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )
        else:
            temp_message = await query.message.reply_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )

    message_authors[temp_message.message_id] = update.effective_user.id

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            if isinstance(best_pp, list) and best_pp:                
                username = user_data["username"]
                stats = user_data["statistics"]
                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )
                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                hours = user_data['statistics']['play_time'] // 3600
                plays = stats.get('play_count') if stats.get('play_count') else "0"                
                accuracy = stats.get('hit_accuracy') if stats.get('hit_accuracy') else "0"
                medals = len(user_data['user_achievements'])
                
                level_data = stats.get('level', {})
                current = level_data.get('current', 0)
                progress = level_data.get('progress', 0)

                level = float(f"{current}.{progress}")

                try:
                    team = user_data['team']['short_name']
                    team_url = f"https://osu.ppy.sh/teams/{user_data['team']['id']}"
                    team_link = f'<a href="{team_url}">{team}</a>'
                except:
                    team_link = '✖️' 
                                
                peak_rank = user_data['rank_highest']['rank']

                def format_osu_date(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S", flag = True) -> str:
                    try:
                        if date_str.endswith("Z"):
                            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        else:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception as e:
                        print(f"Ошибка: {e}")
                        return "N/A"

                    formatted = dt.strftime(fmt)

                    now = datetime.now(timezone.utc)
                    delta = now - dt

                    if delta.days >= 365:
                        years = delta.days // 365
                        ago = f"{years} years ago"
                    elif delta.days >= 30:
                        months = delta.days // 30
                        ago = f"{months} months ago"
                    elif delta.days > 0:
                        ago = f"{delta.days} days ago"
                    else:
                        hours = delta.seconds // 3600
                        ago = f"{hours} hours ago" if hours > 0 else "less than an hour ago"

                    if flag:
                        return f"{formatted} ({ago})"
                    else:
                        return f"({formatted})"
                
                peak_date = format_osu_date(user_data['rank_highest']['updated_at'], "%d.%m.%Y", flag=False)
                joined = format_osu_date(user_data['join_date'], "%Y-%m-%d %H:%M:%S")

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'                 

                text =(
                    f"{user_link}\n\n"
                    f"Accuracy: <code> {accuracy:.2f}%</code>  •  Level:<code> {level}</code>\n"
                    f"Playcount: <code> {plays:,}</code>   (<code>{hours} hrs</code>)\n"
                    f"Medals: <code> {medals} </code> •  Team: {team_link}\n"
                    f"Peak rank: <code> #{peak_rank:,}</code>   {peak_date}\n\n"
                    f"⦿ Joined {joined}\n\n"
                ) 

                if query:
                    for msg_id, author_id in list(message_authors.items()):
                        if author_id == query.from_user.id:
                            try:
                                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=msg_id)
                            except:
                                pass
                            message_authors.pop(msg_id, None)

                    new_msg = await safe_edit_message(
                        temp_message,
                        text,
                        parse_mode="HTML",
                        # reply_markup=get_profile_keyboard("profile")
                    )
                    message_authors[new_msg.message_id] = query.from_user.id
                    return
                else:
                    try:
                        new_msg = await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=temp_message.message_id,
                            text=text,
                            parse_mode="HTML", 
                            # reply_markup=get_profile_keyboard("profile")
                        )
                        message_authors[new_msg.message_id] = update.effective_user.id
                        return
                    except:
                        new_msg = await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            parse_mode="HTML", 
                            # reply_markup=get_profile_keyboard("profile")
                        )
                        message_authors[new_msg.message_id] = update.effective_user.id

            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных или ошибка сети")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при profile (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )