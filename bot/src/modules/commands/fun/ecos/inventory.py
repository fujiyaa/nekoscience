


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *



def get_inventory_pages(user_id: int):
    items = get_inventory(user_id)

    return [
        items[i:i + INVENTORY_PAGE_SIZE]
        for i in range(0, len(items), INVENTORY_PAGE_SIZE)
    ]

async def show_inventory(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)
    pages = get_inventory_pages(user_id)

    if not pages:
        text = (
            f"<b>{user_name}</b>\n"
            f"<code>- баланс: {balance}</code>\n\n"
            "🎒 <b>Инвентарь пуст.</b>"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(owner_id)
        )
        return

    page = max(0, min(page, len(pages) - 1))
    current = pages[page]

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"🎒 <b><u>Инвентарь</u></b>\n\n"
    )

    for item_id, amount in current:
        item = SHOP.get(item_id)
        name = item["name"] if item else item_id
        text += f"{name} <i>×{amount}</i>\n"

    keyboard = []

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_inventory_page_{page - 1}:{owner_id}"
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
                callback_data=f"eco_inventory_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)
    keyboard.append([    
        InlineKeyboardButton(
            "💢 Продать все",
            callback_data=f"eco_sell_inventory_all:{owner_id}"
            )
        ]
    )
    keyboard.append([
        InlineKeyboardButton(
            "Прод. повторки",
            callback_data=f"eco_sell_inventory_duplicates:{owner_id}"
        )]
    )
    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def sell_inventory_all(query):
    
    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_inventory(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🎒 <b>Инвентарь пуст.</b>"        
  
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0

    for item_id, amount in items:

        item = SHOP.get(item_id)

        if not item:
            continue

        price = item.get("price", "2")
        avg_price = price // 2

        total_coins += avg_price * amount

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM inventory_items WHERE telegram_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)
    
    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += f"<b>Продано всe.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )

async def sell_inventory_duplicates(query):
    
    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_inventory(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🎒 <b>Инвентарь пуст.</b>"
  
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        if amount <= 1:
            continue

        item = SHOP.get(item_id)
        if not item:
            continue

        price = item.get("price", "2")
        avg_price = price // 2

        duplicates = amount - 1

        total_coins += avg_price * duplicates

        cur.execute("""
            UPDATE inventory_items
            SET amount = 1
            WHERE telegram_id = ? AND item_id = ?
        """, (user_id, item_id))

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)
    
    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += f"<b>Дубликаты проданы.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )


def get_inventory(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_id, amount
    FROM inventory_items
    WHERE telegram_id = ?
    ORDER BY amount DESC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows

def clear_inventory(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM inventory_items
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()
