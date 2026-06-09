


import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *

from .activity_core import *
from .item_shop import *
from .upgrade_shop import *

from .loot import *

from .inventory import *



def get_storage_pages(user_id: int):
    items = get_storage(user_id)

    return [
        items[i:i + STORAGE_PAGE_SIZE]
        for i in range(0, len(items), STORAGE_PAGE_SIZE)
    ]

async def show_storage(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)
    pages = get_storage_pages(user_id)

    if not pages:
        text = (
            f"<b>{user_name}</b>\n"
            f"<code>- баланс: {balance}</code>\n\n"
            "🕳 <b>Хранилище пустое.</b>"
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
        "🕳 <b><u>Хранилище</u></b>\n\n"
    )

    for item_id, amount in current:
        item = STORAGE_ITEMS_INDEX.get(item_id)
        name = item["name"] if item else item_id
        text += f"{name} <i>×{amount}</i>\n"

    keyboard = []

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_storage_page_{page - 1}:{owner_id}"
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
                callback_data=f"eco_storage_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)
    
    keyboard.append([    
        InlineKeyboardButton(
            "💢 Продать все",
            callback_data=f"eco_sell_storage_all:{owner_id}"
            )
        ]
    )
    keyboard.append([
        InlineKeyboardButton(
            "Прод. повторки",
            callback_data=f"eco_sell_storage_duplicates:{owner_id}"
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


async def sell_storage_all(query):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_storage(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🕳 <b>Хранилище пустое.</b>"

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0
    used_trade_items = set()

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        item = STORAGE_ITEMS_INDEX.get(item_id)
        if not item:
            continue

        price = item.get("coins", (0, 0))[0]
        avg_price = price // 2

        final_price = apply_trade_multiplier(
            user_id,
            item,
            avg_price,
            used_trade_items
        )

        total_coins += final_price * amount

    broken_items = process_trade_item_breaks(
        user_id,
        used_trade_items
    )

    cur.execute(
        "DELETE FROM storage_items WHERE telegram_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)

    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += "<b>Продано все.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    if broken_items:
        text += "\n\n💥 <b>Сломались:</b>\n"

        for item_id in broken_items:
            item = SHOP.get(item_id)

            if item:
                text += f"<code>- {item['name']}</code>\n"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )

async def sell_storage_duplicates(query):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_storage(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🕳 <b>Хранилище пустое.</b>"

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0
    used_trade_items = set()

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        if amount <= 1:
            continue

        item = STORAGE_ITEMS_INDEX.get(item_id)
        if not item:
            continue

        price = item.get("coins", (0, 0))[0]
        avg_price = price // 2

        final_price = apply_trade_multiplier(
            user_id,
            item,
            avg_price,
            used_trade_items
        )

        duplicates = amount - 1

        total_coins += final_price * duplicates

        cur.execute("""
            UPDATE storage_items
            SET amount = 1
            WHERE telegram_id = ? AND item_id = ?
        """, (user_id, item_id))

    broken_items = process_trade_item_breaks(
        user_id,
        used_trade_items
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)

    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += "<b>Дубликаты проданы.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    if broken_items:
        text += "\n\n💥 <b>Сломались:</b>\n"

        for item_id in broken_items:
            item = SHOP.get(item_id)

            if item:
                text += f"<code>- {item['name']}</code>\n"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )
    
def get_storage(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_id, amount
    FROM storage_items
    WHERE telegram_id = ?
    ORDER BY amount DESC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows

def apply_trade_multiplier(user_id, item, base_price, used_trade_items):
    final_price = base_price

    activity = item.get("activity")

    if activity not in ("fish", "mine"):
        return final_price

    trade_item = get_best_trade_item(user_id, activity)

    if not trade_item:
        return final_price

    final_price *= trade_item["mult"]

    used_trade_items.add(trade_item["id"])

    return final_price

def process_trade_item_breaks(user_id, used_trade_items):
    broken = []

    for item_id in used_trade_items:

        item = SHOP.get(item_id)
        if not item:
            continue

        vanish = item.get("effect", {}).get("vanish_chance", 0)

        if random.random() < vanish:
            remove_item(user_id, item_id, 1)
            broken.append(item_id)

    return broken

def get_best_trade_item(user_id, trade_type):
    inventory = get_inventory(user_id)

    best = None

    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        effect = item.get("effect", {})

        if effect.get("trade_type") != trade_type:
            continue

        mult = effect.get("trade_multiplier", 1)

        if best is None or mult > best["mult"]:
            best = {
                "id": item_id,
                "mult": mult,
                "effect": effect
            }

    return best

def clear_storage(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM storage_items
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()