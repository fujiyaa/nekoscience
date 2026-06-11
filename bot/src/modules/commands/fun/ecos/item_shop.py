


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *


def get_shop_categories():
    categories = {}

    for item_id, item in SHOP.items():
        types = [t.strip() for t in item["type"].split(",")]

        for category in types:
            categories.setdefault(category, {})
            categories[category][item_id] = item

    return categories

async def show_shop(query, owner_id):
    categories = get_shop_categories()

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                category.title(),
                callback_data=f"eco_shop_category_{category}:{owner_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        "🛒 Магазин",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_shop_category(
    query,
    category,
    owner_id,
    page=0
):
    categories = get_shop_categories()

    items = list(categories.get(category, {}).items())

    if not items:
        await query.answer("Категория пуста")
        return

    pages = [
        items[i:i + SHOP_PAGE_SIZE]
        for i in range(0, len(items), SHOP_PAGE_SIZE)
    ]

    page = max(0, min(page, len(pages) - 1))

    keyboard = []

    for item_id, item in pages[page]:
        keyboard.append([
            InlineKeyboardButton(
                item["name"],
                callback_data=f"eco_shop_item_{item_id}:{owner_id}"
            )
        ])

    nav_row = []

    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_shop_category_page_{category}|{page - 1}:{owner_id}"
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_shop_category_page_{category}|{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_shop:{owner_id}"
        )
    ])

    await query.edit_message_text(
        f"🛒 Магазин: {category}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_shop_item(query, item_id, status_text, owner_id):    

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    item = SHOP.get(item_id)
    if not item:
        return

    effects = [
        f"<code>• {k}: {v}</code>"
        for k, v in item["effect"].items()
    ]

    text = (
        f"{user_name}\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"<b><u>{item['name']}</u></b>\n\n"
        f"<i>{item['effect_name']}</i>\n\n"
        f"💰 <code>цена:</code> <b>{item['price']}</b>\n"
        f"📦 <code>тип:</code> {item['type']}\n"
        f"<code>🔍 загадочный текст:</code>\n"
        + "\n".join(effects)
    )

    if status_text:
        text = f"{text}\n\n{status_text}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 Купить",
                callback_data=f"eco_buy_{item_id}:{owner_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"eco_shop:{owner_id}"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


def buy_item(user_id: int, item_id: str):
    item = SHOP.get(item_id)

    if not item:
        return False, "❌ Предмет не найден"

    price = item["price"]
    balance = get_balance(user_id)

    if price > 0 and balance < price:
        return False, "❌ Не хватает денег"

    add_coins(user_id, -price)
    add_inventory_item(user_id, item_id)

    return True, "✅ Куплено\n<code>(добавлено в инвентарь)</code>"

def remove_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE inventory_items
        SET amount = amount - ?
        WHERE telegram_id = ? AND item_id = ?
    """, (amount, user_id, item_id))

    cur.execute("""
        DELETE FROM inventory_items
        WHERE telegram_id = ? AND item_id = ?
          AND amount <= 0
    """, (user_id, item_id))

    conn.commit()
    conn.close()
