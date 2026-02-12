


import os
import asyncio
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from ....systems.auth import check_osu_verified
from ....utils.text_format import country_code_to_flag
from ....systems.json_files import load_score_file
from ....utils.calculate import caclulte_cached_entry

from config import COOLDOWN_STATS_COMMANDS, SCORES_DIR



async def start_anime(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(anime(update, context, user_request))

async def anime(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="anime",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    MAX_ATTEMPTS = 3

    user_id = str(update.message.from_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/anime fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", parse_mode="Markdown"
    )

    
    # files = [
    #     f for f in os.listdir(SCORES_DIR)
    #     if os.path.isfile(os.path.join(SCORES_DIR, f)) and f.endswith(".json")
    # ]

    # for i, file in enumerate(files):
    #     file_id, _ = os.path.splitext(file)
    #     entry = load_score_file(file_id)

    #     if entry.get('meta', {}).get('version') == '03022026':
    #         if entry.get('state', {}).get('calculated') != True: 
    #             await caclulte_cached_entry(entry)
    #             print('calc', i)
    #         else:
    #             print('skip', i)


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
              
                total = len(best_pp)
                anime_bg_counter, not_anime_bg_counter = 0, 0

                for score in best_pp:
                    if score.get("is_anime_bg", False):
                        anime_bg_counter += 1
                    else:
                        not_anime_bg_counter += 1

                anime_percent = (anime_bg_counter / total) * 100 if total else 0
                other_percent = (not_anime_bg_counter / total) * 100 if total else 0

                entry_width = len("Anime backgrounds")
                count_width = len("100.0%")

                table_lines = [
                    f"{'Anime backgrounds':<{entry_width}} | {'top100':>{count_width}}",
                    f"{'-'*entry_width}-+-{'-'*count_width}",
                    f"{'anime':<{entry_width}} | {anime_percent:>{count_width}.0f}%",
                    f"{'other':<{entry_width}} | {other_percent:>{count_width}.0f}%"
                ]

                table_text = "\n".join(table_lines)

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

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

                text = f"{user_link}\n\n<pre>{table_text}</pre>"
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"
                    )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Нет данных о топ100`",
                    parse_mode="Markdown"
                )
                return

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при anime (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
