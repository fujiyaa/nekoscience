


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

        modified_table.append((item, weight))

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

        weight = max(MIN_LOOT_WEIGHT, base_weight * luck_bonus)

        weighted_loot.append((item, weight))

    base_fail = ACTIVITIES[activity_name].get("fail_chance", 0.10)

    fail_chance = base_fail * (1 - level * 0.02)

    fail_chance *= max(1 - luck_level * 0.03, 0.25)

    fail_chance *= tool_fail_mod

    fail_chance = max(fail_chance, 0.01)

    if random.random() < fail_chance:
        return None, None, 0, 0, "fail"

    # 4. roll
    chosen_item = random.choices(
        [item for item, _ in weighted_loot],
        weights=[weight for _, weight in weighted_loot],
        k=1
    )[0]

    coins = random.randint(*chosen_item["coins"])
    xp = chosen_item["xp"]

    return (
        chosen_item["id"],
        chosen_item["name"],
        coins,
        xp,
        chosen_item["rarity"]
    )

async def do_activity(query, activity_name):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    now = int(time.time())
    last = get_last_activity(user_id, activity_name)

    tool_level = get_tool_level(user_id, activity_name)

    cooldown_mult = max(1 - (tool_level - 1) * 0.05, 0.30)

    cooldown = int(ACTIVITIES[activity_name]["cooldown"] * cooldown_mult)

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

    level, _, _ = get_progress(user_id, activity_name)
    balance = get_balance(user_id)
    luck_level = get_luck_level(user_id, activity_name)

    item_id, item_name, coins, xp, rarity = roll_loot(
        activity_name,
        level,
        luck_level,
        tool_level
    )

    if rarity == "fail":
        level, current_xp, needed_xp = get_progress(user_id, activity_name)

        text = (
            f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
            f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
            f"<code>- баланс: {balance}</code>\n"
            f"\n"
            f"{ACTIVITIES[activity_name]['fail_action']}\n"
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

    add_storage_item(user_id, item_id=item_id, amount=1)

    base = {"xp": xp, "coins": coins}
    final_xp, final_coins, log = apply_effects(user_id, base, {
        "activity": activity_name
    })

    inventory = get_inventory(user_id)

    reset_item = None
    casino_capsules = []

    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        effect = item.get("effect", {})

        if effect.get("reset_stats"):
            reset_item = item_id

        if effect.get("double_or_nothing"):
            affected = effect.get("affected_thing", "")
            affected_set = set(x.strip() for x in affected.split(","))
            
            casino_capsules.append({
                "item_id": item_id,
                "affected": affected_set
            })

    penalty_text = ""

    if reset_item:
        penalty_text += "\n<code>- использован сброс\n(предмет)</code>"

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
        penalty_text += "\n<code>- опыт не получен\n(негативный баланс)</code>"


    capsule_log = []
    level_change = None
    reset_balance_trigger = False

    targets = {
        "coin": final_coins,
        "xp": final_xp
    }

    for capsule in casino_capsules:
        success = random.random() < 0.5
        affected = capsule["affected"]

        remove_item(user_id, capsule["item_id"], 1)

        capsule_name = SHOP.get(capsule["item_id"], {}).get("name", "капсула")

        result_text = "✔️ Double" if success else "❌ Nothing"

        if "level" in affected:
            level_change = {
                "success": success,
                "value": 2 if success else 1
            }

        for t in affected:
            if t not in targets:
                continue

            if success:
                targets[t] *= 2
            else:
                targets[t] = 0

                if t == "coin":
                    reset_balance_trigger = True

        # if affected == {"coin", "xp"} and success:
        #     targets["coin"] = -abs(targets["coin"])
        #     targets["xp"] = -abs(targets["xp"])

        capsule_log.append(
            f"<code>- {capsule_name}: {result_text}</code>"
        )

    if reset_balance_trigger:
        reset_balance(user_id)

    if level_change:
        if level_change["success"]:
            new_level = level * 2
        else:
            new_level = 1
            targets["xp"] = 0

        set_activity_level(user_id, activity_name, new_level)

    final_coins = targets["coin"]
    final_xp = targets["xp"]

    add_coins(user_id, final_coins)
    add_xp(user_id, activity_name, final_xp)

    level, current_xp, needed_xp = get_progress(user_id, activity_name)

    rarity_emoji = RARITY_EMOJI.get(rarity, "⚪")

    balance = get_balance(user_id)
    broken_items_text = ""
    double_text = ""

    if log["broken"]:
        broken_names = [
            SHOP.get(i, {}).get("name", i)
            for i in log["broken"]
        ]

        broken_items_text = (
            "\n\n💥 Сломались предметы:\n" +
            "\n".join(f"<code>- {n}</code>" for n in broken_names)
        )

    if capsule_log:
        double_text = "\n\nПотрачено:\n" + "\n".join(capsule_log)

    text = (
        f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
        f"<code>- баланс: {balance}</code>\n"
        f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
        f"\n"
        f"{ACTIVITIES[activity_name]['good_action']}: <b>{item_name}</b>\n"
        f"<code>- {rarity_emoji} редкость: {rarity}</code>\n"
        f"<code>- 🪙 деньги: {final_coins}</code>\n"
        f"<code>- ⭐️ опыт: {final_xp} XP</code>\n"
        f"{penalty_text}"
        f"{broken_items_text}"
        f"{double_text}"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_actions_keyboard(user_id)
    )