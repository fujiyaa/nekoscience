


from telegram import Update
from telegram.ext import ContextTypes

from .buttons_level1 import get_keyboard
from .search_v2 import generate_ms_results



async def ms_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != context.user_data.get("ms_user_id"):
        await query.answer("❌ Не твои кнопки", show_alert=True)
        return

    data = query.data.split(":")  # ms_skill:medium
    param_type, value = data

    if param_type == "ms_lazer":
        if not value == 'select_mods_again':
            context.user_data["ms_choices"]["lazer"] = value == "True"
            context.user_data["ms_step"] = 1
        else:            
            context.user_data["ms_step"] = 3

    elif param_type == "ms_skill":
        if not value == 'back':
            context.user_data["ms_choices"]["skill"] = value
            context.user_data["ms_step"] = 2
        else:            
            context.user_data["ms_step"] = 0
           
    elif param_type == "ms_tol":
        if not value == 'back':
            context.user_data["ms_choices"]["tol"] = value
            context.user_data["ms_step"] = 3
        else:            
            context.user_data["ms_step"] = 1

    elif param_type == "ms_mod":
        if not value == 'back':
            context.user_data["ms_choices"]["mod"] = value
            context.user_data["ms_step"] = 4
        else:
            context.user_data["ms_step"] = 2

    step = context.user_data["ms_step"] 

    if step > 3:
        await generate_ms_results(update, context)
    else:     
        try:
            skills = context.user_data.get("skills")
            username = context.user_data.get("ms_username")

            aim = skills.get("aim", 0)
            speed = skills.get("speed", 0)
            acc = skills.get("acc", 0)
            
        except:
            print('Error getting skills | callback_level1')
            return

        if step == 0: 
            text = (
                f'<code>maps_skill v2, поиск по нику: {username}</code>\n'
                f'\n'
                f"acc: <b>{acc:.2f}</b> (Точность)\n"
                f"aim: <b>{aim:.2f}</b> (Аим)\n"
                f"spd: <b>{speed:.2f}</b> (Скорость)\n"
                f'\n'
                f'Выбери версию для поиска:'
            )
        elif step == 1:
            text=(
                f'<code>maps_skill v2, поиск по нику: {username}</code>\n'
                f'\n'
                f"acc: <b>{acc:.2f}</b> × <i>диапазон</i>\n"
                f"aim: <b>{aim:.2f}</b> × <i>...</i>\n"                
                f"spd: <b>{speed:.2f}</b> × <i>...</i>\n"
                f'\n'
                f"Выбери диапазон, который будет применен к скилам:"
            )
        elif step == 2:
            x = context.user_data.get("ms_choices").get('skill')
            x = float(x)/10
            text=(
                f'<code>диапазон {x:.1f}x</code>\n'
                f'\n'
                f"acc: <s>{acc:.2f}</s> → <b>{acc*x:.2f}</b> + <i>погрешность</i>\n"
                f"aim: <s>{aim:.2f}</s> → <b>{aim*x:.2f}</b> + <i>...</i>\n"                
                f"spd: <s>{speed:.2f}</s> → <b>{speed*x:.2f}</b> + <i>...</i>\n"
                f'\n'                
                f"Выбери погрешность диапазона:"
            )
        else:
            x = context.user_data.get("ms_choices").get('skill')
            x = float(x)/10

            y = context.user_data.get("ms_choices").get('tol')
            y = float(y) - 1

            aim2 = aim*x + aim*x*y
            acc2 = acc*x + acc*x*y
            speed2 = speed*x + speed*x*y

            aim1 = aim*x - aim*x*y
            acc1 = acc*x - acc*x*y
            speed1 = speed*x - speed*x*y

            text=(                
                f'<code>диапазон {x:.1f}x, погрешность {y+1:.1f}x</code>\n'
                f'\n'                
                f"acc: <s>{acc:.2f} → {acc*x:.2f}</s>  ⇢  <b>{acc1:.2f}</b> ~ <b>{acc2:.2f}</b>\n"
                f"aim: <s>{aim:.2f} → {aim*x:.2f}</s>  ⇢  <b>{aim1:.2f}</b> ~ <b>{aim2:.2f}</b>\n"
                f"spd: <s>{speed:.2f} → {speed*x:.2f}</s>  ⇢  <b>{speed1:.2f}</b> ~ <b>{speed2:.2f}</b>\n"
                f'\n'
                f"Выбери моды:"
            )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_keyboard(step)
        )
