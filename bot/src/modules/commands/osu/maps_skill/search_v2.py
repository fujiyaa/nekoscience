


from telegram import Update
from telegram.ext import ContextTypes

from .buttons_level1 import get_keyboard as get_fallback_kb
from .buttons_level2 import get_keyboard
from ....actions.messages import safe_edit_query

from .sql_template_v1 import search_beatmaps as search1
from .sql_template_v2 import search_beatmaps as search2

from config import BOT_DIR



async def generate_ms_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("ms_user_id")
    choices = context.user_data.get("ms_choices", {})
    topic_id = context.user_data.get("ms_topic_id", None)

    query = update.callback_query

    if not choices:
        err_text = f"Error getting search settings | search_v2"
        await safe_edit_query(
            query,        
            err_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    try:
        skills = context.user_data.get("skills")

        aim = skills.get("aim", 0)
        speed = skills.get("speed", 0)
        acc = skills.get("acc", 0)
        
    except:
        err_text = f"Error getting skills | search_v2, {e}"
        await safe_edit_query(
            query,        
            err_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        print('Error getting skills | search_v2')
        return

    skill_level = choices.get("skill", "low")
    mod = choices.get("mod", "NM")
    lazer = choices.get("lazer", "True")

    x = choices.get('skill')
    x = float(x)/10

    y = choices.get('tol')
    y = float(y) - 1

    aim2 = aim*x + aim*x*y
    acc2 = acc*x + acc*x*y
    speed2 = speed*x + speed*x*y

    aim1 = aim*x - aim*x*y
    acc1 = acc*x - acc*x*y
    speed1 = speed*x - speed*x*y   

    filters = {
        "aim": (aim1, aim2),
        "speed": (speed1, speed2),
        "acc": (acc1, acc2)
    }

    mods = [mod]
    limit = 800
    offset = 0   

    

    try:
        if not lazer:
            results = search1(
                db_path=f"{BOT_DIR}/beatmaps.db",
                mods=mods,
                filters=filters,
                limit=limit,
                offset=offset,
                lazer=True
            )
        else:
            results = search2(
                db_path=f"{BOT_DIR}/beatmaps_v2.db",
                mods=mods,
                filters=filters,
                limit=limit,
                offset=offset
                # no mode
            )        

    except Exception as e:
        await safe_edit_query( 
            query,       
            f"❌ Ошибка при поиске карт: {e}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    if not results:        
        text=(                
            f'<code>диапазон {x:.1f}x, погрешность {y+1:.1f}x</code>\n'
            f'\n'                
            f"acc: <s>{acc:.2f} → {acc*x:.2f}</s>  ⇢  <b>{acc1:.2f}</b> ~ <b>{acc2:.2f}</b>\n"
            f"aim: <s>{aim:.2f} → {aim*x:.2f}</s>  ⇢  <b>{aim1:.2f}</b> ~ <b>{aim2:.2f}</b>\n"
            f"spd: <s>{speed:.2f} → {speed*x:.2f}</s>  ⇢  <b>{speed1:.2f}</b> ~ <b>{speed2:.2f}</b>\n"
            f'\n'
            f'⛔️ Ничего не найдено ({mod}), попробуй увеличить погрешность, другой диапазон или другие моды:'
            f""
        )
        await safe_edit_query(
            query,
            parse_mode="HTML",
            reply_markup=get_fallback_kb(3),
            text=text
        )
        return

    PAGE_SIZE = 8
    pages = [results[i:i+PAGE_SIZE] for i in range(0, len(results), PAGE_SIZE)]
    context.user_data["ms_pages"] = pages

    aim_base = skills.get("aim", 0)
    speed_base = skills.get("speed", 0)
    acc_base = skills.get("acc", 0)


    current_page = 0

    lines = []

    mods = choices.get("mod", "NM")    
    percent = (float(choices.get('tol')) - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (float(skill_level) / 10)
    lvl_str = f"🔎 {lvl:.1f}x"

    line = f"1️⃣ Acc 2️⃣ Aim 3️⃣ Spd {lvl_str} ±{percent_str} +{mods}\n"
    lines.append(line)

    for beatmap in pages[current_page]:
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
    line = (
        f"\n"
        f"🔼 - скилл карты больше, чем твой\n"
        f"🔽 - скилл карты меньше\n"
        f"🔅 - такой же скилл\n"    
        f"pts - skill points, не равно 100% PP"
    )    
    lines.append(line)
    text = "\n".join(lines)

    keyboard = get_keyboard(current_page, len(pages), user_id)
    
    await safe_edit_query(  
        query,      
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
