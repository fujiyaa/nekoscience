


from telegram import Update
from telegram.ext import ContextTypes

from .buttons_level1 import get_keyboard
from .search import generate_farm_results



async def farm_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != context.user_data.get("farm_user_id"):
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    data = query.data.split(":")  # farm_skill:medium
    param_type, value = data

    if param_type == "farm_skill":
        context.user_data["farm_choices"]["skill"] = value
    elif param_type == "farm_mod":
        context.user_data["farm_choices"]["mod"] = value
    elif param_type == "farm_lazer":
        context.user_data["farm_choices"]["lazer"] = value == "True"
    elif param_type == "farm_tol":
        context.user_data["farm_choices"]["tol"] = value

    context.user_data["farm_step"] += 1
    step = context.user_data["farm_step"]

    if step > 3:
        await query.edit_message_text(f"⏳ @{query.from_user.username}...")
        await generate_farm_results(update, context)
    else:
        if step == 0: text="Клиент?"
        elif step == 1:text="Интенсивность фарма? (80-90% около топскора)"
        elif step == 2:text="Разброс, меньше - точнее уровень прошлого меню, а больше - больше карт за счет увеличения диапазона поиска"
        else:text="Моды, с которыми будет карта"
        await query.edit_message_text(
            text,
            reply_markup=get_keyboard(step)
        )
