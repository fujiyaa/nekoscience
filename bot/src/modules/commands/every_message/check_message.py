


import re
import asyncio
import random

from telegram import Update
from telegram.ext import ContextTypes

from ...systems.logging import log_all_update
from ...systems.auth import verify_osu_user
from ...systems.logging import log_deleted_message
from ..fun.reminders.reminders import start_check_reminders
from modules.commands.osu.beatmap.simulate.text_input import start_simulate_text_handler
from modules.commands.osu.card.beatmap.card import start_beatmap_card
from .start_something import start_osu_link_handler
from ...actions.context import set_message_context

from .blacklist import blacklist
from config import SOURCE_TOPIC_ID, TARGET_CHAT_ID, TARGET_FORWARD_TOPIC_ID
from config import LUCKY_TOPIC_ID, CLIPS_TOPIC_ID
from config import LUCKY_DICE_EMOJI, CHANCE_DICE, UNLUCKY_MESSAGES

DICE_EMOJI = '🎲'
SLOT_EMOJI = '🎰'
BALL_EMOJI = '🏀'
DART_EMOJI = '🎯'

LUCKY_EMOJIS = {DICE_EMOJI, SLOT_EMOJI, BALL_EMOJI, DART_EMOJI}



async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await log_all_update(update)              
        
        print(f"chat {update.effective_chat.id}, topic {getattr(update.effective_message, 'message_thread_id', None)}")

        try:
            text = update.message.text.strip()
            telegram_id = str(update.message.from_user.id)

            if re.fullmatch(r"[A-Z0-9]{6}", text):    
                username = await verify_osu_user(text, telegram_id)

                if username:
                    await update.message.reply_text(
                            f"{username} теперь привязан"
                        )
        except:
            pass

        try:
            await start_check_reminders(update, context)
            await start_osu_link_handler(update, context)
            await start_simulate_text_handler(update, context)
            await start_beatmap_card(update, context, False)
        except:
            pass
            
        text_to_check = (update.effective_message.text or update.effective_message.caption or "").lower()
        if "mapset" in text_to_check:            
            match = re.search(r'id(\d+)', text_to_check)
            if match:
                mapset_id = int(match.group(1))
                
                set_message_context(
                    update, 
                    reply=False, 
                    mapset_id=mapset_id,
                    origin_call_user_id=update.effective_user.id,
                )
        elif "profile" in text_to_check:            
            match = re.search(r'id(\d+)', text_to_check)
            if match:
                username_text = int(match.group(1))
                
                set_message_context(
                    update, 
                    reply=False, 
                    profile_player_username=username_text,
                    origin_call_user_id=update.effective_user.id,
                )


        if any(bad_word in text_to_check for bad_word in blacklist):
            try:
                await update.effective_message.delete()
                msg = await update.effective_chat.send_message(f"Сообщение удалено — содержит запрещённое слово.")

                async def delete_notice(message):
                    await asyncio.sleep(15)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Ошибка при удалении уведомления: {e}")
                asyncio.create_task(delete_notice(msg))

                user_str = f"{update.effective_message.from_user.full_name} (id: {update.effective_message.from_user.id})" if update.effective_message.from_user else "Неизвестный пользователь"
                log_deleted_message(user_str, update.effective_message.text or update.effective_message.caption or "<нет текста>")
                print("Удалено сообщение с запрещённым словом")
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
            return 
        
        if update.effective_chat.id == TARGET_CHAT_ID:
            thread_id = getattr(update.effective_message, 'message_thread_id', None)

            if thread_id == CLIPS_TOPIC_ID:
                message = update.effective_message
                text = message.text or message.caption or ""
                urls = []

                if message.entities:
                    for ent in message.entities:
                        if ent.type == "url":
                            urls.append(message.text[ent.offset: ent.offset + ent.length])
                        elif ent.type == "text_link" and ent.url:
                            urls.append(ent.url)

                special_links = [u for u in urls if u and ("youtube.com" in u or "youtu.be" in u or "twitch.tv" in u or "issou.best" in u)]

                if message.video or special_links:
                    pass
                else:
                    try:
                        await message.forward( chat_id=TARGET_CHAT_ID, message_thread_id=TARGET_FORWARD_TOPIC_ID )
                        await message.delete()
                    except Exception as e:
                        print(f"Ошибка при if thread_id == CLIPS_TOPIC_ID: {e}")
                  
            if update.effective_message.dice and update.effective_message.dice.emoji in LUCKY_EMOJIS:
                if random.random() < 0.03: 
                    try:
                        chosen = update.effective_message.dice.emoji
                        await update.effective_chat.send_dice(
                                        emoji=chosen,
                                        message_thread_id=update.effective_message.message_thread_id
                                    )
                    except Exception as e:
                        print(e)                     

            if thread_id == LUCKY_TOPIC_ID:
                if update.effective_message.dice and update.effective_message.dice.emoji == LUCKY_DICE_EMOJI:
                    if random.random() < CHANCE_DICE:
                        try:
                            await update.effective_message.delete()

                            response = await update.effective_chat.send_message(
                                random.choice(UNLUCKY_MESSAGES),
                                message_thread_id=LUCKY_TOPIC_ID
                            )

                            async def delete_response(resp):
                                await asyncio.sleep(10)
                                try:
                                    await resp.delete()
                                except Exception as e:
                                    print(f"Ошибка при удалении ответа: {e}")

                            asyncio.create_task(delete_response(response))

                            user_str = f"{update.effective_message.from_user.full_name} (id: {update.effective_message.from_user.id})" if update.effective_message.from_user else "Неизвестный пользователь"
                            log_deleted_message(user_str, f"Dice emoji: {update.effective_message.dice.emoji}, value: {update.effective_message.dice.value}")
                            print("Удалено сообщение с кубиком 🎰")
                        except Exception as e:
                            print(f"Ошибка при удалении кубика: {e}")

                
            if thread_id == SOURCE_TOPIC_ID:
                message = update.effective_message
                if not (message.document or message.photo):
                    try:
                        await message.forward(
                            chat_id=TARGET_CHAT_ID,
                            message_thread_id=TARGET_FORWARD_TOPIC_ID
                        )
                        await message.delete()

                        user_str = f"{message.from_user.full_name} (id: {message.from_user.id})" if message.from_user else "Неизвестный пользователь"
                        text = message.text or message.caption or "<нет текста>"
                        log_deleted_message(user_str, f"Перенесено сообщение: {text}")
                        print("Сообщение без вложений перенесено и удалено")

                    except Exception as e:                    
                        print(f"Ошибка при пересылке и удалении сообщения: {e}")

                else:
                    print("Есть вложение (файл или картинка), не трогаем")

    except: print(e)
    