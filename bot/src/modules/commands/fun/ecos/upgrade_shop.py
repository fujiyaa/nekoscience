


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *



def get_upgrades_pages():
    items = list(UPGRADES.items())

    return [
        items[i:i + UPGRADES_PAGE_SIZE]
        for i in range(0, len(items), UPGRADES_PAGE_SIZE)
    ]

async def show_upgrades(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    pages = get_upgrades_pages()

    if not pages:
        await query.edit_message_text("🧬 Апгрейды отсутствуют")
        return

    page = max(0, min(page, len(pages) - 1))
    current = pages[page]

    keyboard = []

    for upgrade_id, upgrade in current:
        keyboard.append([
            InlineKeyboardButton(
                upgrade["name"],
                callback_data=f"eco_upgrade_{upgrade_id}:{owner_id}"
            )
        ])

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_upgrades_page_{page - 1}:{owner_id}"
            )
        )

    nav.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_upgrades_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        "🧬 Апгрейды",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_upgrade_item(query, upgrade_id, status_text, owner_id):
    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    level = get_user_field(
        user_id,
        upgrade["field"],
        0
    )

    if "tool" in upgrade_id:
        level = max(level, 1)

    next_level = level + 1
    price = get_upgrade_price(upgrade_id, next_level)

    text = (
        f"{user_name}\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"<b><u>{upgrade['name']}</u></b>\n\n"
        f"<i>{upgrade['effect_name']}</i>\n"
        f"<i>Улучшение с {level} до уровня {next_level}</i>\n\n"
        f"💰 <code>цена:</code> <b>{price}</b>\n"
        f"📦 <code>тип:</code> улучшение"
    )

    if status_text:
        text = f"{text}\n\n{status_text}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🧬 Купить",
                callback_data=f"eco_upgrade_buy_{upgrade_id}:{owner_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"eco_upgrades:{owner_id}"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

def get_upgrade_price(upgrade_id, level):
    data = UPGRADES[upgrade_id]

    return int(
        data["base_price"] *
        (data["price_mult"] ** (level - 1))
    )


def buy_upgrade(user_id: int, upgrade_id: str):

    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return False, "❌ Апгрейд не найден"

    level = get_user_field(
        user_id,
        upgrade["field"],
        0
    )

    if "tool" in upgrade_id:
        level = max(level, 1)

    next_level = level + 1

    price = get_upgrade_price(
        upgrade_id,
        next_level
    )

    balance = get_balance(user_id)

    if balance < price:
        return False, "💸 Не хватает денег"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE users
        SET
            coins = coins - ?,
            {upgrade['field']} = {upgrade['field']} + 1
        WHERE telegram_id = ?
        """,
        (
            price,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return True, (
        f"✅ Успешно улучшено"
    )

def get_upgrade_info(user_id: int, upgrade_id: str):

    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return None

    level = get_upgrade_level(
        user_id,
        upgrade_id
    )

    next_price = get_upgrade_price(
        upgrade_id,
        level + 1
    )

    return {
        "id": upgrade_id,
        "name": upgrade["name"],
        "level": level,
        "next_price": next_price,
    }

def get_upgrade_level(user_id: int, upgrade_id: str):
    data = UPGRADES.get(upgrade_id)

    if not data:
        return 0

    field = data["field"]

    return get_user_field(
        user_id,
        field,
        0
    )

