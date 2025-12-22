


import os
import json

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from .buttons_level2 import get_keyboard

from .....config import USERS_SKILLS_FILE



async def farm_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action, user_id, page = data
    user_id = int(user_id)
    page = int(page)

    if query.from_user.id != user_id:
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    pages = context.user_data.get("farm_pages", [])
    if not pages:
        await query.edit_message_text("❌ Ошибка: данные не найдены")
        return

    saved_name = await check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
    else:
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    lines = []
    choices = context.user_data.get("farm_choices", {})
    skill_level = choices.get("skill", "1")
    percent = (float(choices.get("tol", 1.2)) - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[page]:
        map_id = beatmap[0]
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

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

    text = "\n".join(lines)

    keyboard = get_keyboard(page, len(pages), user_id)  # <-- тоже page

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )