


import os
import json
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from .buttons_level2 import get_keyboard
from .sql_template import search_beatmaps

from config import BOT_DIR, USERS_SKILLS_FILE



async def generate_farm_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("farm_user_id")
    choices = context.user_data.get("farm_choices", {})
    topic_id = context.user_data.get("farm_topic_id", None)

    if not choices:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Ошибка: параметры поиска не выбраны"
        )
        return

    saved_name = await check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
        aim = skills.get("aim_total", 0)
        speed = skills.get("speed_total", 0)
        acc = skills.get("acc_total", 0)
        print(f"    Навыки пользователя {saved_name}: aim={aim}, speed={speed}, acc={acc}")
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Навыки пользователя не найдены. Создайте карточку через /card."
        )
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")


    skill_level = choices.get("skill", "low")
    mod = choices.get("mod", "NM")
    lazer = choices.get("lazer", "True")
    tol = float(choices.get("tol", 1.2))

    if skill_level == "1":
        base_start, base_end = 0.35, 0.45
    elif skill_level == "2":
        base_start, base_end = 0.45, 0.55
    elif skill_level == "3":
        base_start, base_end = 0.55, 0.65
    elif skill_level == "4":
        base_start, base_end = 0.65, 0.75
    elif skill_level == "5":
        base_start, base_end = 0.75, 0.85
    elif skill_level == "6":
        base_start, base_end = 0.85, 0.95
    elif skill_level == "7":
        base_start, base_end = 0.95, 1.05
    elif skill_level == "8":
        base_start, base_end = 1.05, 1.15
    elif skill_level == "9":
        base_start, base_end = 1.15, 1.25
    else:  # high
        base_start, base_end = 1.25, 1.35

    static_mult = 1.0
    start_mult = base_start / (tol*static_mult)
    end_mult = base_end * (tol*static_mult)

    #if skill_level == "floor":
    #    base_start, base_end = 0.4, 0.6
    #elif skill_level == "low":
    #    base_start, base_end = 0.6, 0.8
    #elif skill_level == "medium":
    #    base_start, base_end = 0.8, 1.0
    #else:  # high
    #    base_start, base_end = 1.0, 1.3

    #start_mult = base_start / tol 
    #end_mult = base_end * tol      

    filters = {
        "aim": (aim * start_mult, aim * end_mult),
        "speed": (speed * start_mult, speed * end_mult),
        "acc": (acc * start_mult, acc * end_mult)
    }

    mods = [mod]
    limit = 800
    offset = 0   

    try:
        results = search_beatmaps(
            db_path=f"{BOT_DIR}/beatmaps.db",
            mods=mods,
            filters=filters,
            limit=limit,
            offset=offset,
            lazer=lazer
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text=f"❌ Ошибка при поиске карт: {e}"
        )
        return

    if not results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="🚮 Ничего не найдено, попробуй увеличить разброс или другой уровень скилов."
        )
        return

    PAGE_SIZE = 8
    pages = [results[i:i+PAGE_SIZE] for i in range(0, len(results), PAGE_SIZE)]
    context.user_data["farm_pages"] = pages

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    # --- Отправляем первую страницу ---
    current_page = 0
    lines = []
    percent = (tol - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[current_page]:
        map_id = beatmap[0]
        lazer = beatmap[1].upper()
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        # сравниваем с базовыми
        def cmp_symbol(val, base):
            if val > base + 15:
                return "🔼"
            elif val < base - 15:
                return "🔽"
            else:
                return "🔅"

        symbols = "".join([            
            cmp_symbol(acc, acc_base),
            cmp_symbol(aim, aim_base),
            cmp_symbol(speed, speed_base),
        ])

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"https://myangelfujiya.ru/darkness/direct?id={map_id}"

        line = f"{total_str}pts {symbols} [http://osu.p...]({url}) | [🔗]({url_2})   +{mods}"
        lines.append(line)
    line = """\n            🔼 — скилл карты больше твоего
            🔽 — твой скилл больше, карта легче
            🔅 — такой же скилл, как твой"""
    lines.append(line)
    text = "\n".join(lines)

    keyboard = get_keyboard(current_page, len(pages), user_id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=topic_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True

    )
