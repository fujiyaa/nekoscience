


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .....utils.text_format import format_stats, make_header, row

from config import COOLDOWN_STATS_COMMANDS

MAX_ATTEMPTS = 3  



async def start_compare_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(compare_profile(update, context, user_request))

async def compare_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="pc",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context
        )
    if not can_run:
        return
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            temp_message = await update.message.reply_text(f"`Загрузочка... `{attempt}/{MAX_ATTEMPTS}", parse_mode="Markdown") 
            break
        except Exception as e:
            print(e)
            return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
    
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Загрузочка... {attempt}/{MAX_ATTEMPTS}`", 
                    parse_mode="Markdown")

            args_text = " ".join(context.args)

            if args_text.count("#") == 1:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Ошибка: найден только один #. Должно быть либо 0, либо 2.`",
                    parse_mode="Markdown"
                )
                return
            elif args_text.count("#") == 2:
                parts = args_text.split("#")
                username1 = parts[1].strip()
                username2 = parts[2].strip()
            else:
                parts = args_text.split()
                if len(parts) != 2:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=(
                            "Использование: `/pc <ник1> <ник2>`\n\n"
                            "Пример: `/pc Fujiya Vaxei`\n"
                            "Или с пробелами: `/pc #Fujiya #cs Pro 2014`"
                        ),
                        parse_mode="Markdown"
                    )
                    return
                username1, username2 = parts[0], parts[1]
            
            token = await get_osu_token()
            async def fetch_data(name):
                try:
                    user_data = await asyncio.wait_for(get_user_profile(name, token=token), timeout=10)
                    user_id = user_data["id"]
                    best_pp = await asyncio.wait_for(get_top_100_scores(name, token, user_id), timeout=10)
                    return user_data, best_pp
                except:
                    return None, None

            user1, top1 = await fetch_data(username1)
            user2, top2 = await fetch_data(username2)

            if not user1 or not user2:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Что-то пошло не так...`",
                    parse_mode="Markdown"
                )
                return
           
            p1 = format_stats(user1, top1)
            p2 = format_stats(user2, top2)

            header, sep = make_header(p1['name'], p2['name'])
            table = [header, sep]

            table.append(row(p1['rank'], "Rank", p2['rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['peak_rank'], "Peak rank", p2['peak_rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['pp'], "PP", p2['pp'], higher_is_better=True, suffix="pp", fmt="{:,.0f}"))
            table.append(row(p1['acc'], "Accuracy", p2['acc'], higher_is_better=True, suffix="%", fmt="{:,.2f}"))
            table.append(row(p1['level'], "Level", p2['level'], higher_is_better=True, fmt="{:.2f}"))
            table.append(row(p1['hours'], "Playtime", p2['hours'], higher_is_better=True, suffix="hrs", fmt="{:,}"))
            table.append(row(p1['playcount'], "Playcount", p2['playcount'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_count'], "PC peak", p2['max_count'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['maps'], "Maps played", p2['maps'], higher_is_better=True, fmt="{:,}"))
            # table.append(row(p1['anime_bg_counter'], "Anime top%", p2['anime_bg_counter'], higher_is_better=False, suffix="%", fmt="{:,}"))
            table.append(row(p1['ranked_score']/1e9, "Ranked score", p2['ranked_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_score']/1e9, "Total score", p2['total_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_hits'], "Total hits", p2['total_hits'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['hpp'], "Hits/play", p2['hpp'], higher_is_better=True, fmt="{:,.2f}"))
            table.append(row(p1['ss'], "SS count", p2['ss'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['s'], "S count", p2['s'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['a'], "A count", p2['a'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_combo'], "Max Combo", p2['max_combo'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['medals'], "Medals", p2['medals'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['top1_pp'], "Top1 PP", p2['top1_pp'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_diff'], "PP spread", p2['pp_diff'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_avg_all'], "Avg PP", p2['pp_avg_all'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_pp_per_month'], "PP per month", p2['avg_pp_per_month'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_count_per_month'], "PC per month", p2['avg_count_per_month'], higher_is_better=True, fmt="{:,.0f}"))
            table.append(row(p1['join_date'], "Join date", p2['join_date'], higher_is_better=False, is_date=True))
            table.append(row(p1['followers'], "Followers", p2['followers'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['mapping'], "Mapping subs", p2['mapping'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['posts'], "Forum posts", p2['posts'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['replays'], "Replays seen", p2['replays'], higher_is_better=True, fmt="{:,}"))

            text = "```\n" + "\n".join(table) + "\n```"

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=temp_message.message_id,
                text=text,
                parse_mode="Markdown"
            )
            return
        
        except Exception as e:
            print(f"Ошибка при pc (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
