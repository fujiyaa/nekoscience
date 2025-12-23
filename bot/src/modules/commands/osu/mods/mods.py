


import asyncio
from collections import Counter, defaultdict

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from ....systems.auth import check_osu_verified
from ....utils.text_format import format_blocks_percent, format_blocks_pp, country_code_to_flag
from ....utils.osu_conversions import format_mods

from config import COOLDOWN_STATS_COMMANDS



async def start_mods(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mods(update, context, user_request)) 

async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="mods",
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
                "Использование: `/mods fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
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
                best_pp = "N/A"
                print(e)


            if isinstance(best_pp, list) and best_pp:
                mod_counter = Counter()
                combo_counter = Counter()
                # combo_pp_sum = defaultdict(float)
                combo_pp_weighted_sum = defaultdict(float)

                for score in best_pp:
                    mods = score.get("mods", [])
                    combo = format_mods(mods)

                    if mods:
                        for m in mods:
                            mod_counter[m] += 1
                    else:
                        mod_counter["NM"] += 1

                    combo_counter[combo] += 1

                    pp_value = score.get("pp", 0.0) or 0.0
                    weight_percent = score.get("weight_percent", 0.0) or 0.0

                    # combo_pp_sum[combo] += pp_value
                    combo_pp_weighted_sum[combo] += pp_value * (weight_percent / 100)

                total_scores = len(best_pp)

                fav_mods_str = format_blocks_percent(mod_counter, total_scores, per_row=4)
                fav_combos_str = format_blocks_percent(combo_counter, total_scores, per_row=3)
                # profit_combos_str = format_blocks_pp(combo_pp_sum, per_row=3)
                weighted_combos_str = format_blocks_pp(combo_pp_weighted_sum, per_row=3)

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
               
                text = (
                    f"{user_link}\n\n"
                    "⦿ <b><u>Top100 mods:</u></b>\n\n"
                    f"<b>Favourite mods</b>\n{fav_mods_str}\n\n"
                    f"<b>Favourite mod combinations</b>\n{fav_combos_str}\n\n"
                    # f"<b>Profitable mod combinations (pp)</b>\n{profit_combos_str}\n\n"
                    f"<b>Profitable mod combinations (pp)</b>\n{weighted_combos_str}"
                )

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
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при mods (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
