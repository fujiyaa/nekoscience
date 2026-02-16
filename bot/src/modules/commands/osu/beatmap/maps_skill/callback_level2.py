


from telegram import Update
from telegram.ext import ContextTypes

from .buttons_level2 import get_keyboard



async def ms_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    _action, user_id, page = data
    user_id = int(user_id)
    page = int(page)

    if query.from_user.id != user_id:
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    pages = context.user_data.get("ms_pages", [])
    if not pages:
        await query.edit_message_text("❌ Ошибка: данные не найдены")
        return
        
    try:
        skills = context.user_data.get("skills")

        aim_base = skills.get("aim", 0)
        speed_base = skills.get("speed", 0)
        acc_base = skills.get("acc", 0)
        
    except:
        print('Error getting skills | callback_level2')
        return

    choices = context.user_data.get("ms_choices", {})
    skill_level = choices.get("skill", "low")

    lines = []

    lazer = choices.get("lazer", "True")
    mods = choices.get("mod", "NM")
    percent = (float(choices.get('tol')) - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (float(skill_level) / 10)
    lvl_str = f"🔎 {lvl:.1f}x"

    line = f"1️⃣ Acc 2️⃣ Aim 3️⃣ Spd {lvl_str} ±{percent_str} +{mods}\n"
    lines.append(line)

    for beatmap in pages[page]:
        if not lazer:
            map_id = beatmap[0]
            mods = beatmap[2]
            aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]
        else:
            map_id = beatmap[0]
            mods = beatmap[1]
            aim, speed, acc = beatmap[2], beatmap[3], beatmap[4]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        def cmp_symbol(val, base):
            if val > base + 10:
                return "🔼"
            elif val < base - 10:
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

        line = f"*{total_str}*pts {symbols} id`{map_id}` • [ссылка]({url}) • [direct]({url_2})"
        lines.append(line)

    text = "\n".join(lines)

    keyboard = get_keyboard(page, len(pages), user_id)  # <-- тоже page

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )