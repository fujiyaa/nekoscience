


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
from .storage import *



init_db()
migrate_add_forest()
migrate_add_battle()
build_item_index()

async def main_menu(update, context):

    user_id = update.message.from_user.id
    user_name = update.message.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    progress_lines = []

    for activity_name, activity in ACTIVITIES.items():

        level, xp, needed_xp = get_progress(user_id, activity_name)

        progress_lines.append(
            f"<code>- {activity['name']} lvl.{level} "
            f"({xp}/{needed_xp})</code>"
        )

    progress_text = "\n".join(progress_lines)

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n"        
        f"{progress_text}"        
    )
    
    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )

async def main_menu_query(query, actions: bool = False):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    progress_lines = []

    for activity_name, activity in ACTIVITIES.items():

        level, xp, needed_xp = get_progress(user_id, activity_name)

        progress_lines.append(
            f"<code>- {activity['name']} lvl.{level} "
            f"({xp}/{needed_xp})</code>"
        )

    progress_text = "\n".join(progress_lines)

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n"
        f"{progress_text}"        
    )

    if actions:
        reply_markup=get_actions_keyboard(user_id)
    else:
        reply_markup=get_main_keyboard(user_id)

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def economy_callback(update, context):

    query = update.callback_query
    
    data = query.data
    user_id = query.from_user.id

    if ":" in data:
        payload, owner_id = data.rsplit(":", 1)
        try:
            owner_id = int(owner_id)
        except ValueError:
            return await query.answer("ошибка?", show_alert=True)

        if owner_id != user_id:
            return await query.answer("не твои кнопки, создай свои командой /economy", show_alert=True)
    else:
        return await query.answer("не твои кнопки, ошибка?", show_alert=True)

    await query.answer()

    data = payload

    if data == "eco_actions":
        await main_menu_query(query, True)

    elif data == "eco_main_menu":
        await main_menu_query(query, False)

    elif data == "eco_fish":
        await do_activity(query, "fish")

    elif data == "eco_mine":
        await do_activity(query, "mine")

    elif data == "eco_forest":
        await do_activity(query, "forest")

    elif data == "eco_battle":
        await do_activity(query, "battle")

    elif data == "eco_inventory":
        await show_inventory(query, owner_id)

    elif data == "eco_storage":
        await show_storage(query, owner_id)
    
    elif data == "eco_shop":
        await show_shop(query, owner_id)

    elif data.startswith("eco_shop_category_page_"):
        payload = data.replace(
            "eco_shop_category_page_",
            ""
        )

        category, page = payload.split("|")

        await show_shop_category(
            query,
            category,
            owner_id,
            int(page)
        )

    elif data.startswith("eco_shop_category_"):
        category = data.replace(
            "eco_shop_category_",
            ""
        )

        await show_shop_category(
            query,
            category,
            owner_id
        )

    elif data.startswith("eco_inventory_page_"):
        page = int(data.replace("eco_inventory_page_", ""))
        await show_inventory(query, owner_id, page)

    elif data.startswith("eco_upgrades_page_"):
        page = int(data.replace("eco_upgrades_page_", ""))
        await show_upgrades(query, owner_id, page)

    elif data.startswith("eco_storage_page_"):
        page = int(data.replace("eco_storage_page_", ""))
        await show_storage(query, owner_id, page)

    elif data.startswith("eco_shop_item_"):
        item_id = data.replace(
            "eco_shop_item_",
            ""
        )

        await show_shop_item(
            query,
            item_id,
            None,
            owner_id
        )

    elif data.startswith("eco_buy_"):
        item_id = data.replace("eco_buy_", "")

        success, text = buy_item(
            query.from_user.id,
            item_id
        )

        await show_shop_item(
            query,
            item_id,
            text,
            owner_id
        )

    elif data == "eco_upgrades":
        await show_upgrades(query, owner_id)

    elif data.startswith("eco_upgrade_") and not data.startswith("eco_upgrade_buy_"):

        upgrade_id = data.replace(
            "eco_upgrade_",
            ""
        )

        await show_upgrade_item(
            query,
            upgrade_id,
            None,
            owner_id
        )

    elif data.startswith("eco_upgrade_buy_"):

        upgrade_id = data.replace(
            "eco_upgrade_buy_",
            ""
        )

        success, text = buy_upgrade(
            query.from_user.id,
            upgrade_id
        )

        await show_upgrade_item(
            query,
            upgrade_id,
            text,
            owner_id
        )

    elif data.startswith("eco_sell_inventory_duplicates"):
        await sell_inventory_duplicates(query)

    elif data.startswith("eco_sell_inventory_all"):
        await sell_inventory_all(query)

    elif data.startswith("eco_sell_storage_duplicates"):
        await sell_storage_duplicates(query)

    elif data.startswith("eco_sell_storage_all"):
        await sell_storage_all(query)

    elif data == "eco_top":
        await show_top_players(query, owner_id)