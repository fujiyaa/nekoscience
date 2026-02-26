


import os
import random
import logging
import temp
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message, delete_response

from config import COOLDOWN_PICS_COMMANDS, ARCHER_BOT, CHANCE_PIC
from config import IMAGES_DIR, LUCKY_TOPIC_ID, TARGET_CHAT_ID, fail_texts



async def random_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="random_image",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_PICS_COMMANDS,           
            update=update,
            context=context
        )
        if not can_run:
            return

        if update.effective_chat.id != TARGET_CHAT_ID:
            user_msg = update.message

            if random.random() > CHANCE_PIC:                
                bot_msg = await safe_send_message(update, random.choice(fail_texts))

                if bot_msg:
                    asyncio.create_task(delete_response([user_msg, bot_msg], delay=30))

            else:
                data = temp.load_images_data()
                all_images = data.get("all", [])

                if not all_images:
                    await safe_send_message(update, "❌ В папке нет картинок.")
                    return

                available_images = list(set(all_images))

                selected_image = random.choice(available_images)
                image_path = os.path.join(IMAGES_DIR, selected_image)

                try:
                    with open(image_path, "rb") as img:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=img,
                            message_thread_id=update.message.message_thread_id
                        )
                except FileNotFoundError:
                    logging.error(f"Файл не найден: {image_path}")
                    await safe_send_message(update, "❌ Ошибка: картинка не найдена.")
                    return
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото: {e}")
                    await safe_send_message(update, "❌ Ошибка при отправке фото.")
                    return
        else:
            if update.message.message_thread_id != LUCKY_TOPIC_ID:
                await safe_send_message(update, "⚠️ Команда доступна только в определённом топике.")
                return

            if update.effective_user.id == ARCHER_BOT:
                await safe_send_message(update, "⚠️ Команда недоступна для ботов.")
                return

            user_msg = update.message

            if random.random() > CHANCE_PIC:                
                bot_msg = await safe_send_message(update, random.choice(fail_texts))

                if bot_msg:
                    asyncio.create_task(delete_response([user_msg, bot_msg], delay=60))

            else:
                data = temp.load_images_data()
                all_images = data.get("all", [])
                used_images = data.get("used", [])

                if not all_images:
                    await safe_send_message(update, "❌ В папке нет картинок.")
                    return

                available_images = list(set(all_images) - set(used_images))

                if not available_images:
                    #data["used"] = []
                    #save_images_data(data)
                    await safe_send_message(update, "✅ Все картинки были использованы")
                    return

                selected_image = random.choice(available_images)
                image_path = os.path.join(IMAGES_DIR, selected_image)

                try:
                    with open(image_path, "rb") as img:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=img,
                            message_thread_id=update.message.message_thread_id
                        )
                except FileNotFoundError:
                    logging.error(f"Файл не найден: {image_path}")
                    await safe_send_message(update, "❌ Ошибка: картинка не найдена.")
                    return
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото: {e}")
                    await safe_send_message(update, "❌ Ошибка при отправке фото.")
                    return

                used_images.append(selected_image)
                data["used"] = used_images
                temp.save_images_data(data)

    except Exception as e:
        logging.error(f"Ошибка в random_image: {e}")
        # await safe_send_message(update, "❌ Произошла непредвиденная ошибка.")