


import random
import time

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *

from .activity_core import *
from .item_shop import *
from .upgrade_shop import *

from .inventory import *
from .storage import *


def apply_slot(user_id, value, best_item, buff_key, log, slot_name, is_random=False):
    if not best_item:
        return value, log

    item_id = best_item["id"]
    effect = best_item["effect"]

    # сломался предмет
    if random.random() < effect.get("vanish_chance", 0):
        remove_item(user_id, item_id, 1)

        log["broken"].append(item_id)
        log["selected"][slot_name] = "BROKEN"
        return value, log

    # обычный множитель
    if not is_random:
        value = int(value * effect[buff_key])
    else:
        # random multiplier
        value = int(value * random.uniform(1.0, effect[buff_key]))

    log["selected"][slot_name] = item_id
    return value, log

def apply_effects(user_id: int, base, context):
    inventory = get_inventory(user_id)

    best = {
        "xp_buff": None,
        "xp_random": None,
        "coin_buff": None,
        "coin_random": None,
        "trade": None
    }

    log = {
        "base": base.copy(),
        "selected": {},
        "broken": [],
        "steps": [],
        "final": {}
    }

    xp = base["xp"]
    coins = base["coins"]

    # 1. выбор лучших предметов по слотам
    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        effect = item.get("effect", {})

        # XP buff
        if "xp_buff" in effect:
            if (best["xp_buff"] is None or
                effect["xp_buff"] > best["xp_buff"]["effect"]["xp_buff"]):
                best["xp_buff"] = {"id": item_id, "effect": effect}

        # XP random
        if "xp_multiplier_random" in effect:
            if (best["xp_random"] is None or
                effect["xp_multiplier_random"] > best["xp_random"]["effect"]["xp_multiplier_random"]):
                best["xp_random"] = {"id": item_id, "effect": effect}

        # COIN buff
        if "coin_buff" in effect:
            if (best["coin_buff"] is None or
                effect["coin_buff"] > best["coin_buff"]["effect"]["coin_buff"]):
                best["coin_buff"] = {"id": item_id, "effect": effect}

        # COIN random
        if "coin_multiplier_random" in effect:
            if (best["coin_random"] is None or
                effect["coin_multiplier_random"] > best["coin_random"]["effect"]["coin_multiplier_random"]):
                best["coin_random"] = {"id": item_id, "effect": effect}

        # TRADE
        if "negative_coin_chance" in effect:
            if (best["trade"] is None or
                effect["negative_coin_chance"] > best["trade"]["effect"]["negative_coin_chance"]):
                best["trade"] = {"id": item_id, "effect": effect}

    # 2. XP slots
    xp, log = apply_slot(user_id, xp, best["xp_buff"], "xp_buff", log, "xp_buff")
    xp, log = apply_slot(user_id, xp, best["xp_random"], "xp_multiplier_random", log, "xp_random", is_random=True)

    # 3. COINS slots
    coins, log = apply_slot(user_id, coins, best["coin_buff"], "coin_buff", log, "coin_buff")
    coins, log = apply_slot(user_id, coins, best["coin_random"], "coin_multiplier_random", log, "coin_random", is_random=True)

    # 4. TRADE
    if best["trade"]:
        item_id = best["trade"]["id"]
        effect = best["trade"]["effect"]

        if random.random() < effect["negative_coin_chance"]:
            coins = -coins

            log["steps"].append({
                "type": "trade_penalty",
                "item": item_id,
                "lost_coins": coins
            })

        log["selected"]["trade"] = item_id

    log["final"] = {
        "xp": xp,
        "coins": coins
    }

    return xp, coins, log

def apply_tool_luck(tool_level: int, loot_table: list):

    if tool_level <= 1 or not loot_table:
        return [(item, item["weight"]) for item in loot_table], 1.0

    luck_power = 1 + (tool_level - 1) * 0.06

    modified_table = []

    for item in loot_table:
        weight = item["weight"]
        rarity = item.get("rarity", "обычное")

        if rarity == "редкое":
            weight *= (1 + (luck_power - 1) * 0.8)
        elif rarity == "очень редкое":
            weight *= (1 + (luck_power - 1) * 1.2)
        elif rarity == "эпическое":
            weight *= (1 + (luck_power - 1) * 1.6)
        elif rarity == "легендарное":
            weight *= (1 + (luck_power - 1) * 2.2)

        modified_table.append((item, int(weight)))

    fail_modifier = max(1 - (tool_level - 1) * 0.04, 0.6)

    return modified_table, fail_modifier

def roll_loot(
    activity_name: str,
    level: int,
    luck_level: int,
    tool_level: int
):
    loot_table = get_available_loot(activity_name, level)

    if not loot_table:
        return None, None, 0, 0, "none"

    modified_table, tool_fail_mod = apply_tool_luck(
        tool_level,
        loot_table
    )

    weighted_loot = []

    for item, base_weight in modified_table:

        rarity = item.get("rarity", "обычное")

        luck_bonus = 1 + luck_level * {
            "редкое": 0.05,
            "очень редкое": 0.08,
            "эпическое": 0.12,
            "легендарное": 0.18
        }.get(rarity, 0)

        weight = max(1, int(base_weight * luck_bonus))

        weighted_loot.append((item, weight))

    base_fail = ACTIVITIES[activity_name].get("fail_chance", 0.10)

    fail_chance = base_fail * (1 - level * 0.02)

    fail_chance *= max(1 - luck_level * 0.03, 0.25)

    fail_chance *= tool_fail_mod

    fail_chance = max(fail_chance, 0.01)

    if random.random() < fail_chance:
        return None, None, 0, 0, "fail"

    # 4. roll
    total_weight = sum(w for _, w in weighted_loot)
    roll = random.randint(1, total_weight)

    current = 0

    for item, weight in weighted_loot:
        current += weight
        if roll <= current:
            coins = random.randint(*item["coins"])
            xp = item["xp"]
            return item["id"], item["name"], coins, xp, item["rarity"]

    item = random.choice(loot_table)
    return item["id"], item["name"], random.randint(*item["coins"]), item["xp"], item["rarity"]

async def do_activity(query, activity_name):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    now = int(time.time())
    last = get_last_activity(user_id, activity_name)


    tool_level = get_tool_level(
        user_id,
        activity_name
    )

    cooldown_mult = max(
        1 - (tool_level - 1) * 0.05,
        0.30
    )

    cooldown = int(
        ACTIVITIES[activity_name]["cooldown"] *
        cooldown_mult
    )


    if now - last < cooldown:        
        activity_title_text = ACTIVITIES[activity_name]["name"]
        text = (
            f"<b>{user_name}</b>\n\n"
            f"{activity_title_text}\n"
            f"<code>- жди {cooldown - (now - last)} сек.</code>\n"
            f"<code>- или улучши 🧬</code>\n"
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_actions_keyboard(user_id)
        )
        return

    set_last_activity(user_id, activity_name)

    level, _, _ = get_progress(
        user_id,
        activity_name
    )

    balance = get_balance(user_id)
    
    luck_level = get_luck_level(
        user_id,
        activity_name
    )

    item_id, item_name, coins, xp, rarity = roll_loot(
        activity_name,
        level,
        luck_level,
        tool_level
    )

    activity_fail_action_text = ACTIVITIES[activity_name]["fail_action"]

    if rarity == "fail":
        level, current_xp, needed_xp = get_progress(
            user_id,
            activity_name
        )
        
        text = (
            f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
            f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
            f"<code>- баланс: {balance}</code>\n"            
            f"\n"
            # f"{activity_title_text}\n"        
            # f"\n"
            f"{activity_fail_action_text}\n"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_actions_keyboard(user_id)
        )
        return
    
    mult = RARITY_MULTIPLIER.get(rarity, 1.0)

    coins = int(coins * level_multiplier(level) * mult)
    xp = int(xp * level_multiplier(level) * mult)

    add_storage_item(
        user_id,
        item_id=item_id,
        amount=1
    )

    base = {
        "xp": xp,
        "coins": coins
    }

    final_xp, final_coins, log = apply_effects(user_id, base, {
        "activity": activity_name
    })

    inventory = get_inventory(user_id)

    reset_item = None

    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        if item.get("effect", {}).get("reset_stats"):
            reset_item = item_id
            break
    
    penalty_text = ""

    if reset_item:
        penalty_text += (
            "\n<code>- использован сброс\n(предмет)</code>"
        )

        reset_player(user_id)

        clear_inventory(user_id)
        clear_storage(user_id)
                      
        final_xp = 0
        final_coins = 0

        log["steps"].append({
            "type": "reset_triggered",
            "item": reset_item
        })

    future_balance = balance + final_coins    

    if future_balance <= MAX_NEGATIVE_BALANCE:
        final_xp = 0
        penalty_text += (
            "\n<code>- опыт не получен\n(негативный баланс)</code>"
        )

    # print(json.dumps(log, indent=4, ensure_ascii=False))

    add_coins(user_id, final_coins)
    add_xp(user_id, activity_name, final_xp)

    level, current_xp, needed_xp = get_progress(
        user_id,
        activity_name
    )
    
    raity_emoji = RARITY_EMOJI.get(rarity, "⚪")    
    activity_good_action_text = ACTIVITIES[activity_name]["good_action"]

    broken_items_text = ""

    if log["broken"]:
        broken_names = []

        for item_id in log["broken"]:
            item = SHOP.get(item_id)
            broken_names.append(item["name"] if item else item_id)

        broken_items_text = (
            "\n\n💥 Сломались предметы:\n" +
            "\n".join(f"<code>- {name}</code>" for name in broken_names)
        )

    text = (
        f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
        f"<code>- баланс: {balance + final_coins}</code>\n"
        f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
        f"\n"        
        # f"{activity_title_text}\n"        
        # f"\n"
        f"{activity_good_action_text}: <b>{item_name}</b>\n"
        f"<code>- {raity_emoji} редкость: {rarity}</code>\n"
        f"<code>- 🪙 деньги: {final_coins} </code>\n"
        f"<code>- ⭐️ опыт: {final_xp} XP</code>\n"
        f"{penalty_text}" 
        f"{broken_items_text}"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_actions_keyboard(user_id)
    )