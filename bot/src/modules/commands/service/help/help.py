


import asyncio

from telegram import Update, MessageEntity
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....actions.rich import send_rich_message

from config import COOLDOWN_HELP_COMMAND, HELP_TEXTS, help_hint, help_text



async def start_help(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(help(update, context, user_request))

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    try:
        can_run = await check_user_cooldown(
            command_name="help",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_HELP_COMMAND,           
            update=update,
            context=context
        )
        if not can_run:
            return
                
        args = context.args  
        if args:
            topic = args[0].lower()
            full_text = HELP_TEXTS.get(topic, f"❓ Нет справки для '{topic}'\n\n" + HELP_TEXTS["default"])
            max_attempts = 3
            for _ in range(max_attempts):
                await update.message.reply_text(full_text, parse_mode='HTML')
                return
        else:            
            # full_text = help_text + help_hint        
            # entities = [
            #     MessageEntity(
            #         type="expandable_blockquote",
            #         offset=0,                     
            #         length=tg_len(help_text)
            #     )
            # ]        
            # max_attempts = 3
            # for _ in range(max_attempts):
            #     await update.message.reply_text(full_text, entities=entities)
            #     return

            markdown = f"""
# 📖 Weakness Bot

<details>
<summary>🎮 Последние игры</summary>

### /recent | /rs 📖
Последние игры игрока

### /fix
Фикс последней игры

</details>

<details>
<summary>📑 Старые игры</summary>

### /score | /s 📖
Игры на карте из чата

### Ссылка на скор
Можно просто отправить ссылку на score.osu и бот обработает её без команды.

</details>

<details>
<summary>👤 Профиль</summary>

### @WeakoBot user ...
Инлайн поиск игроков

### /profile | /p
Профиль игрока

### /pc
Сравнение профилей

</details>

<details>
<summary>📊 Статистика из топ-100</summary>

### /beatmaps | /b 💾
Теги, юзертеги и прочая статистика

### /nochoke | /n 🔧📖
Топ без миссов

### /ppfire | /fire 📖
Костёр PP

### /mods
Статистика модов

### /mappers
Топ мапперов

### /anime
Процент аниме-фонов

### /aim
Aim-слоп

### /speed
Speed-слоп

### /nishometr
Показатель нишевости

</details>

<details>
<summary>📈 Средняя статистика</summary>

### /average | /a
Минимум, среднее и максимум скоров

### /minmax | /mx
Минимум и максимум со ссылками

</details>

<details>
<summary>🗺 Карты</summary>

### @WeakoBot map ...
Инлайн поиск карт

### /music
MP3 из карты

### /bg
Фон карты

### /simulate
Расчёт PP

### /maps_skill
Подбор карт по скиллам

</details>

<details>
<summary>🖼 Карточки</summary>

### /card | /c
Карточка профиля

### /skills
Карточка навыков

### /cardtop
Топ-5 PP

### /map
Карточка карты

</details>

<details>
<summary>⚔️ Daily Challenge</summary>

### /challenge 💾
Главное меню дейли-челленджа

</details>

<details>
<summary>🕹 Игры</summary>

### /higherlower | /hl 💾📖
Угадай характеристику случайного скора

### /economy | /e 💾
Экономическая мини-игра

</details>

<details>
<summary>👥 Чат</summary>

### /topchat | /l
Топ участников чата

</details>

<details>
<summary>⚙️ Настройки osu!</summary>

### /settings
Настройки бота

### /name
Ссылка на авторизацию

</details>

---

# 🔧 Другое

<details>
<summary>Общие команды</summary>

### /roll
Случайное число или выбор варианта

### /reminders
Напоминания для чата

### /doubt | /blacks
Отправляет гифки

### /gn
Гемблинг картинок

### /mod 📖
Модерация чата (если доступно)

### /minecraft | /mc
Статус Minecraft-сервера

### /ping
Проверка доступности бота

### /uptime
Время работы бота

</details>
"""

            await send_rich_message(
                chat_id=update.effective_chat.id,
                markdown=markdown
            )
        
    except Exception as e:
        print(f"Ошибка при help: {e}")

def tg_len(text: str) -> int:
            return len(text.encode("utf-16-le")) // 2
