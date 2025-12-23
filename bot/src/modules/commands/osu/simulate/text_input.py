


import re
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .actions import clear_s_chat
from .utils import calc_accuracy, calculate_rank, update_hits, format_text
from .buttons import get_simulate_keyboard
from ....external.localapi import get_map_stats_neko_api
from ....actions.messages import delete_user_message

from config import VALID_MODS, INVALID_MODS_COMBINATIONS, ABSOLUTELY_FORBIDDEN
from config import sessions_simulate



async def start_simulate_text_handler(update, context):
    try:
        asyncio.create_task(simulate_text_handler(update, context))            
    except Exception as e: print(e)

async def simulate_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sess = sessions_simulate.get(user_id)

    if not sess or not sess["waiting"]:
        return

    param_name = sess["waiting"]
    info = sess["schema"][param_name]   
    value = update.message.text.strip()
    
  
    if info["type"] == "mods":
        cleaned = re.sub(r"\s+", "", value)  
        if not re.fullmatch(r"[A-Za-z]{2,}", cleaned):
            msg = await update.message.reply_text(
                "❌ Неверный формат"
            )
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return

        pairs = re.findall(r"[A-Za-z]{2}", cleaned)
        if not pairs:
            msg = await update.message.reply_text(
                "❌ Неверный формат"
            )
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return

        seen = set()
        unique_pairs = []
        for p in pairs:
            up = p.upper()
            if up not in VALID_MODS:
                msg = await update.message.reply_text(f"❌ Недопустимый мод: {up}")
                clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
                return
            if up not in seen:
                seen.add(up)
                unique_pairs.append(up)

        pairs_set = set(unique_pairs)
        for forbidden in INVALID_MODS_COMBINATIONS:
            if forbidden.issubset(pairs_set):
                msg = await update.message.reply_text(
                    f"❌ Эти моды не могут встречаться вместе: {', '.join(forbidden)}"
                )
                clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
                return
            
        if ABSOLUTELY_FORBIDDEN & set(unique_pairs):
            if len(unique_pairs) > 1:
                msg = await update.message.reply_text(
                    "❌ NM не может сочетаться ни с чем"
                )
                clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
                return

        value = "".join(unique_pairs)
        num = str(value)
    elif info["type"] == "accuracy":
        value_clean = value.replace(",", ".")
        
        try:
            num = float(value_clean)
        except ValueError:
            msg = await update.message.reply_text("❌ Неверный формат: нужно число от 0 до 100")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return

        if not (0 <= num <= 100):
            msg = await update.message.reply_text("❌ Число должно быть от 0 до 100")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
    elif info["type"] == "rate":
        value_clean = value.replace(",", ".")
        
        try:
            num = float(value_clean)
        except ValueError:
            msg = await update.message.reply_text("❌ Неверный формат: нужно число от 0 до 100")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return

        if not (0.5 <= num <= 2):
            msg = await update.message.reply_text("❌ Число должно быть от 0.50 до 2.00")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
    elif info["type"] == "combo":
        value_clean = value.strip()

        if not value_clean.isdigit():
            msg = await update.message.reply_text("❌ Неверный формат: нужно целое число")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        if not (int(info["min"]) <= int(value_clean) <= int(info["max"])): 
            msg = await update.message.reply_text(f"❌ Неверный формат: сейчас комбо может быть от {info['min']} до {info['max']}")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = int(value_clean)
    elif info["type"] == "300k":
        value_clean = value.strip()

        if not value_clean.isdigit():
            msg = await update.message.reply_text("❌ Неверный формат: нужно целое число")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        if not (int(info["min"]) <= int(value_clean) <= int(info["max"])):
            msg = await update.message.reply_text(f"❌ Неверный формат: сейчас может быть от {info['min']} до {info['max']}")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = int(value_clean)
    elif info["type"] == "100k":
        value_clean = value.strip()

        
        if not value_clean.isdigit():
            msg = await update.message.reply_text("❌ Неверный формат: нужно целое число")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        if not (int(info["min"]) <= int(value_clean) <= int(info["max"])):
            msg = await update.message.reply_text(f"❌ Неверный формат: сейчас может быть от {info['min']} до {info['max']}")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = int(value_clean)
    elif info["type"] == "50k":
        value_clean = value.strip()

        if not value_clean.isdigit():
            msg = await update.message.reply_text("❌ Неверный формат: нужно целое число")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        if not (int(info["min"]) <= int(value_clean) <= int(info["max"])):
            msg = await update.message.reply_text(f"❌ Неверный формат: сейчас может быть от {info['min']} до {info['max']}")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = int(value_clean)
    elif info["type"] == "miss":
        value_clean = value.strip()

        if not value_clean.isdigit():
            msg = await update.message.reply_text("❌ Неверный формат: нужно целое число")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        if not (int(info["min"]) <= int(value_clean) <= int(info["max"])):
            msg = await update.message.reply_text(f"❌ Неверный формат: сейчас может быть от {info['min']} до {info['max']}")
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = int(value_clean)
    elif info["type"] == "lazer":
        value_clean = value.strip().lower() 

        true_values = {"да", "yes", "true", "1"}
        false_values = {"нет", "no", "false", "0"}

        if value_clean in true_values:
            value = True
        elif value_clean in false_values:
            value = False
        else:
            msg = await update.message.reply_text(
                "❌ Неверный формат: допустимо только Да/Нет или True/False"
            )
            clear_s_chat(update, context, msg.chat.id, msg.message_id, 0, 5)
            return
        num = value


    value = num

    if info["type"] == "miss" or info["type"] == "100k" or info["type"] == "50k" or info["type"] == "300k":
        update_hits(sess, info["type"], int(value))
    else:   
        sess["params"][param_name] = value
        sess["waiting"] = None

    if sess.get("hint_id"):
        try:
            await context.bot.delete_message(chat_id=sess["chat_id"], message_id=sess["hint_id"])
        except:
            pass
        sess["hint_id"] = None
    
    asyncio.create_task(delete_user_message(update, context, delay=0))
    try:        
        acc = sess["params"].get("Точность")
        miss = sess["params"].get("мисс")    
        stats = {
            "n300": sess["params"].get("300"),
            "n100": sess["params"].get("100"),
            "n50": sess["params"].get("50"),
        }
        if info["type"] == 'accuracy':
            stats = {
            "n300": None,
            "n100": None,
            "n50": None,
            }      
            sess["300_changed"] = False
            sess["100_changed"] = False
            sess["50_changed"] = False
            sess["miss_changed"] = False
        if info["type"] == "miss" or info["type"] == "100k" or info["type"] == "50k" or info["type"] == "300k":
            acc = None

        #neko API 
        payload = {
            "map_path": str(sess["beatmap"]), 
            
            "n300": int(v) if (v := stats["n300"]) is not None else 0,
            "n100": int(v) if (v := stats["n100"]) is not None else 0,
            "n50": int(v) if (v := stats["n50"]) is not None else 0,
            "misses": int(miss or 0),                   
            
            "mods": str(sess["params"].get("Моды")), 
            "combo": int(sess["params"].get("Комбо") or 0),      
            "accuracy": float(acc or 0),    
            
            "lazer": bool(sess["params"].get("Лазер")),          
            "clock_rate": float(sess["params"].get("Скорость") or 1.0),  

            "custom_ar": float(sess['values'].get("ar") or 0.0),
            "custom_cs": float(sess['values'].get("cs") or 0.0),
            "custom_hp": float(sess['values'].get("hp") or 0.0),
            "custom_od": float(sess['values'].get("od") or 0.0),
        }

        try:
            pp_data = await get_map_stats_neko_api(payload)

            pp = pp_data.get("pp")
            choke = pp_data.get("no_choke_pp")
            max_pp = pp_data.get("perfect_pp")

            stars = pp_data.get("star_rating")
            max_combo = pp_data.get("perfect_combo")
            expected_bpm = pp_data.get("expected_bpm")

            n300 = pp_data.get("n300")
            n100 = pp_data.get("n100") 
            n50 = pp_data.get("n50")
            expected_miss = pp_data.get("misses")

            skill_aim = pp_data.get("aim")
            skill_acc = pp_data.get("acc")
            skill_speed = pp_data.get("speed")

        except Exception as e:
            print(f"neko API failed: {e}")    
        
              


        sess["acc"] = skill_acc
        sess["aim"] = skill_aim
        sess["speed"] = skill_speed

        sess["params"]["300"] = n300
        sess["params"]["100"] = n100
        sess["params"]["50"] = n50
        sess["params"]["мисс"] = expected_miss
        sess["params"]["Точность"] = calc_accuracy(n300, n100, n50, expected_miss)
        sess["grade"] = calculate_rank(n300, n100, n50, miss, sess["params"]["Лазер"])

        await context.bot.edit_message_text(            
            text=format_text(user_id, pp, max_pp, stars, sess["map_combo"], expected_bpm, n300, n100, n50, expected_miss),
            chat_id=sess["chat_id"],
            message_id=sess["message_id"],
            reply_markup=get_simulate_keyboard(user_id),
            parse_mode="Markdown" 
        )
    except Exception as e:
        print(e)
