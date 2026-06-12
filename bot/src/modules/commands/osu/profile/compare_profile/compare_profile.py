


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....commands.service import set_name
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .....utils.text_format import format_stats, make_header, row
from .....actions.rich import edit_rich_message

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
            temp_message = await update.message.reply_text(f"`Загрузка...`", parse_mode="Markdown") 
            break
        except Exception as e:
            print(e)
            return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            saved_osu_name = await check_osu_verified(str(update.effective_user.id))

            args_text = " ".join(context.args).strip()

            username1, username2 = parse_pc(args_text, saved_osu_name)

            if not username1:
                await set_name(update, context)
                await temp_message.delete()
                return
            if not username1 or not username2:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=("Против себя: `/pc ник1 (в том числе с пробелами)`\n\n" 
                          "Два ника: `/pc ник1 ник2`\n" 
                          "Два ника: `/pc #ник1 #ник2 (для ников с пробелами)`"),
                    parse_mode="Markdown"
                )
                return
            
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

            def fmt(v):
                if isinstance(v, float):
                    return float(f"{v:.2f}".rstrip("0").rstrip("."))
                return v
            
            def fmt_value(v, fmt):
                if fmt is None:
                    return str(v)

                try:
                    if isinstance(v, (int, float)) and "bn" not in fmt:
                        return fmt.format(v)
                    return fmt.format(v)
                except:
                    return str(v)

            p1_score = 0
            p2_score = 0

            def format_cell(label, key, higher_is_better, fmt, p1, p2, scale=1.0, suffix=None):

                nonlocal p1_score, p2_score

                a = p1.get(key)
                b = p2.get(key)

                if isinstance(a, (int, float)) and scale != 1.0:
                    a = a / scale
                    b = b / scale

                va = fmt_value(a, fmt)
                vb = fmt_value(b, fmt)

                if key == "join_date":
                    return f"| {label} | {va} | {vb} |"

                if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    return f"| {label} | {va} | {vb} |"

                if higher_is_better:
                    win_a = a > b
                    win_b = b > a
                else:
                    win_a = a < b
                    win_b = b < a

                def wrap(v, tag):
                    return f"<{tag}>{v}</{tag}>"

                if win_a:
                    va = wrap(va, "b")
                    vb = wrap(vb, "code")
                    p1_score += 1
                elif win_b:
                    va = wrap(va, "code")
                    vb = wrap(vb, "b")
                    p2_score += 1

                return f"| {label} | {va} | {vb} |"


            rows_config = [                       
                ("Рейтинг", "rank", False, "{:,}"),                
                ("PP", "pp", True, "{:,.0f}"),
                ("Топскор", "top1_pp", True, "{:,.2f}"),
                ("Точность", "acc", True, "{:,.2f}"),                
                ("Макс. комбо", "max_combo", True, "{:,}"),                
                ("Попад./игру", "hpp", True, "{:,.2f}"), 
                ("Игры", "playcount", True, "{:,}"),
                ("Плейтайм (часы)", "hours", True, "{:,}"),
                ("Карт сыграно", "maps", True, "{:,}"),
                
                ("Макс. рейтинг", "peak_rank", False, "{:,}"),
                ("PP разброс", "pp_diff", True, "{:,.2f}"),
                ("Среднее PP", "pp_avg_all", True, "{:,.2f}"),
                ("PP в месяц", "avg_pp_per_month", True, "{:,.2f}"),
                ("Игр в месяц", "avg_count_per_month", True, "{:,.0f}"),
                ("Игры (пик)", "max_count", True, "{:,}"),
                ("SS", "ss", True, "{:,}"),
                ("S", "s", True, "{:,}"),
                ("A", "a", True, "{:,}"),
                 
                ("Уровень", "level", True, "{:.2f}"),
                ("Медали", "medals", True, "{:,}"),                                   
                ("Рейт. очки (млрд)", "ranked_score", True, "{:.2f}", 1e9, "bn"),
                ("Всего очков(млрд)", "total_score", True, "{:.2f}", 1e9, "bn"),
                ("Попаданий (млн)", "total_hits", True, "{:.2f}", 1e6, "bn"),
                ("Фолловеры", "followers", True, "{:,}"),
                ("Маппинг ф-ры", "mapping", True, "{:,}"),
                ("Форум посты", "posts", True, "{:,}"),
                ("Просм. реплеев", "replays", True, "{:,}"),
                ("Регистрация", "join_date", False, None),
            ]

            table = [
                f"| | {p1['name']} | {p2['name']} |",
                "|:--|:-:|:-:|",
            ]

            for item in rows_config:
                if len(item) == 4:
                    label, key, hib, fmt = item
                    scale = 1.0
                elif len(item) == 6:
                    label, key, hib, fmt, scale, suffix = item
                else:
                    label, key, hib, fmt, scale, suffix = (*item, 1.0, None)

                table.append(
                    format_cell(label, key, hib, fmt, p1, p2, scale)
                )

            winner_text = ""

            if p1_score > p2_score:
                winner_text = f"{p1['name']} побеждает {p1_score}:{p2_score}"
            elif p2_score > p1_score:
                winner_text = f"{p2['name']} побеждает {p2_score}:{p1_score}"
            else:
                winner_text = f"ничья {p1_score}:{p2_score}"

            text = "\n".join(table)

            tables = split_markdown_table(text, splits=[9, 18])

            table1, table2, table3 = tables

            text = f"""
<details open>
<summary>📊 {winner_text}</summary>

{table1}

</details>

<details>
<summary>📈 Раздел динамичности</summary>

{table2} 

</details>

<details>
<summary>👥 Социальное и гринд</summary>

{table3}

</details>
"""

            await edit_rich_message(
                update,
                message_id=temp_message.message_id,
                markdown=text
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

def parse_pc(args_text: str, saved_name: str | None):
    args_text = args_text.strip()

    if "#" in args_text:
        parts = [p.strip() for p in args_text.split("#") if p.strip()]
        
        if len(parts) == 1:
            if not saved_name:
                return None, None
            return saved_name, parts[0]

        # #user1 #user2 → user1 vs user2
        if len(parts) >= 2:
            return parts[0], parts[1]

    parts = args_text.split()

    if len(parts) == 2:
        return parts[0], parts[1]

    if len(parts) >= 1:
        if not saved_name:
            return None, None
        return saved_name, " ".join(parts)

    return None, None

def split_markdown_table(text: str, splits: list[int]):

    lines = text.strip().split("\n")

    header = lines[0]
    align = lines[1]
    rows = lines[2:]

    result = []

    prev = 0
    for idx, split in enumerate(splits + [len(rows)]):

        chunk = rows[prev:split]
        if not chunk:
            prev = split
            continue

        if idx == 0:
            part = [header, align] + chunk
        else:
            part = [chunk[0], align] + chunk[1:]

        result.append("\n".join(part))
        prev = split

    return result