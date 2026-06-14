


import re
import asyncio

from telegram import Update
from .....utils.osu_conversions import get_mods_info, apply_mods_to_stats
from .actions import clear_s_chat
from .....actions.messages import delete_user_message
from .utils import calc_accuracy, calculate_rank, update_hits, format_text
from .buttons import get_simulate_keyboard
from .....external.localapi import get_map_stats_neko_api
from .....actions.messages import delete_user_message
from .....actions.rich import edit_rich_message

from config import VALID_MODS, INVALID_MODS_COMBINATIONS, ABSOLUTELY_FORBIDDEN
from config import sessions_simulate
from typing import Callable, Any

Validator = Callable[[str, dict], Any]

format_error_text = "❌ Неверный формат"



async def start_simulate_text_handler(update, context):
    try:
        asyncio.create_task(simulate_text_handler(update, context))            
    except Exception as e: print(e)

async def simulate_text_handler(update: Update, context):
    user_id = update.effective_user.id
    sess = sessions_simulate.get(user_id)

    if not sess or not sess["waiting"]:
        return

    param = sess["waiting"]
    info = sess["schema"][param]

    ok, value, error = await parse_input(update, context, sess, info)

    if not ok:
        return
    
    decide_api_mode(sess, info)

    apply_value(sess, param, info, value)

    await cleanup_messages(update, context, sess)

    await recalculate_simulation(sess)

    await render_simulation(update, context, sess)

async def parse_input(update, context, sess, info):
    validator = VALIDATORS[info["type"]]

    try:
        value = validator(update.message.text.strip(), info)

        return True, value, None

    except ValueError as e:
        hint_msg = await context.bot.edit_message_text(
            chat_id=sess["chat_id"],
            message_id=sess["hint_id"],
            text=f'{e}, выбери параметр для редактирования заново'
        )
        await delete_user_message(update, context, 1)
        sess["waiting"] = None
        return False, None, str(e)
    
def validate_accuracy(text, info) -> float:
    text = text.replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{format_error_text}")

    if not 0 <= value <= 100:
        raise ValueError(f"{format_error_text}")

    return float(value)

def validate_float(text, info) -> float:
    text = text.replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{format_error_text}")

    if not info["min"] <= value <= info["max"]:
        raise ValueError(f"{format_error_text}")

    return float(value)

def validate_rate(text, info) -> float:
    text = text.replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{format_error_text}")

    if not 0.5 <= value <= 2:
        raise ValueError(f"{format_error_text}")

    return float(value)

def validate_int(text, info) -> int:
    if not text.isdigit():
        raise ValueError(f"{format_error_text}")

    value = int(text)

    if not info["min"] <= value <= info["max"]:
        raise ValueError(f"{format_error_text}")

    return int(value)

def validate_bool(text, info) -> bool:
    text = text.strip().lower()

    true_values = {"да", "yes", "true", "1"}
    false_values = {"нет", "no", "false", "0"}

    if text in true_values:
        return True
    if text in false_values:
        return False

    raise ValueError(f"{format_error_text}")

def validate_mods(text, info):
    cleaned = re.sub(r"\s+", "", text)

    if not re.fullmatch(r"[A-Za-z]{2,}", cleaned):
        raise ValueError(f"{format_error_text}")

    pairs = re.findall(r"[A-Za-z]{2}", cleaned)

    if not pairs:
        raise ValueError(f"{format_error_text}")

    seen = set()
    unique = []

    for mod in pairs:
        mod = mod.upper()

        if mod not in VALID_MODS:
            raise ValueError(f"❌ Недопустимый мод: {mod}")

        if mod not in seen:
            seen.add(mod)
            unique.append(mod)

    mods = set(unique)

    for forbidden in INVALID_MODS_COMBINATIONS:
        if forbidden.issubset(mods):
            raise ValueError(
                f"❌ Эти моды не могут встречаться вместе: {', '.join(forbidden)}"
            )

    if ABSOLUTELY_FORBIDDEN & mods and len(unique) > 1:
        raise ValueError(
            "❌ NM не может сочетаться ни с чем"
        )

    return "".join(unique)

def apply_value(sess, param, info, value):

    if info["type"] in {
        "miss",
        "300k",
        "100k",
        "50k"
    }:
        update_hits(sess, info["type"], value)
    else:
        sess["params"][param] = value
        sess["waiting"] = None

def build_payload(sess):

    payload = {

        "map_path": str(sess["beatmap"]),

        "mods": sess["params"]["Моды"],

        "combo": int(sess["params"].get("Комбо") or 0),

        "accuracy": sess["params"]["Точность"],

        "lazer": sess["params"]["Лазер"],

        "clock_rate": sess["params"]["Скорость"],

        "custom_ar": sess["params"]["ar"],

        "custom_cs": sess["params"]["cs"],

        "custom_hp": sess["params"]["hp"],

        "custom_od": sess["params"]["od"],
    }

    if sess['api_mode_accuracy']:
        payload.update({
            "n300": None,
            "n100": None,
            "n50": None,
            "misses": None,
        })
    
    else:
        payload.update({
            "n300": int(sess["params"]["300"]),
            "n100": int(sess["params"]["100"]),
            "n50": int(sess["params"]["50"]),
            "misses": sess["params"]["мисс"],
        })

    return payload

def decide_api_mode(sess, info):
    
    if info["type"] in {
        "miss",
        "300k",
        "100k",
        "50k"
    }: 
        sess['api_mode_accuracy'] = False

    elif info["type"] == "accuracy":
        sess['api_mode_accuracy'] = True
    

def apply_pp_result(sess, data):

    sess["pp"] = data["pp"]
    sess["no_choke_pp"] = data["no_choke_pp"]
    sess["perfect_pp"] = data["perfect_pp"]

    sess["star_rating"] = data["star_rating"]
    sess["perfect_combo"] = data["perfect_combo"]
    sess["expected_bpm"] = data["expected_bpm"]

    sess["acc"] = data["acc"]
    sess["aim"] = data["aim"]
    sess["speed"] = data["speed"]

    sess["params"]["300"] = data["n300"]
    sess["params"]["100"] = data["n100"]
    sess["params"]["50"] = data["n50"]
    sess["params"]["мисс"] = data["misses"]

    sess["params"]["Точность"] = calc_accuracy(
        data["n300"],
        data["n100"],
        data["n50"],
        data["misses"],
    )

    sess["grade"] = calculate_rank(
        data["n300"],
        data["n100"],
        data["n50"],
        data["misses"],
        sess["params"]["Лазер"],
    )

async def cleanup_messages(update, context, sess):
    if sess.get("hint_id"):
        try:
            await context.bot.delete_message(
                chat_id=sess["chat_id"],
                message_id=sess["hint_id"],
            )
        except:
            pass

        sess["hint_id"] = None

    asyncio.create_task(
        delete_user_message(update, context, delay=0)
    )

async def recalculate_simulation(sess):
    payload = build_payload(sess)

    try:
        data = await get_map_stats_neko_api(payload)

    except RuntimeError as e:
        print(f"[neko API error] {e}")

        sess["api_error"] = True
        return

    apply_pp_result(sess, data)

    apply_attrs(sess)

def apply_attrs(sess):
    
    speed_multiplier, hr_active, ez_active = get_mods_info(sess["params"]["Моды"])

    if sess['params']['Скорость'] != 1.0:
        speed_multiplier = sess['params']['Скорость']

    sess["expected_bpm"], sess['params']['ar'], sess['params']['od'], sess['params']['cs'], sess['params']['hp'] = apply_mods_to_stats(
        sess["expected_bpm"], 
        sess['schema']['ar']['default'], 
        sess['schema']['od']['default'], 
        sess['schema']['cs']['default'], 
        sess['schema']['hp']['default'], 
        speed_multiplier=speed_multiplier, 
        hr=hr_active, 
        ez=ez_active
    )
    
    sess['hit_length_updated'] = int(round(float(sess['hit_length'])) / speed_multiplier)
    

async def render_simulation(update: Update, context, sess):
    data = sess
    
    await edit_rich_message(
        update,
        message_id=data["message_id"],
        markdown=format_text(
            update.effective_user.id,
            data["pp"],
            data["perfect_pp"],
            data["star_rating"],
            data["map_combo"],
            data["expected_bpm"],
            data["params"]["300"],
            data["params"]["100"],
            data["params"]["50"],
            data["params"]["мисс"],
        ),      
        reply_markup=get_simulate_keyboard(update.effective_user.id)        
    )

VALIDATORS = {
    "mods": validate_mods,
    "accuracy": validate_accuracy,
    "rate": validate_rate,
    "combo": validate_int,
    "300k": validate_int,
    "100k": validate_int,
    "50k": validate_int,
    "miss": validate_int,
    "lazer": validate_bool,
    "cs": validate_float,
    "ar": validate_float,
    "od": validate_float,
    "hp": validate_float,
}