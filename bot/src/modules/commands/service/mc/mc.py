


import asyncio

from mcstatus import JavaServer

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_HELP_COMMAND



async def start_mc(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mc(update, context, user_request))

async def mc(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    try:
        can_run = await check_user_cooldown(
            command_name="mc",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_HELP_COMMAND,
            update=update,
            context=context
        )
        if not can_run:
            return

        ip = "myangelfujiya.ru"

        loop = asyncio.get_running_loop()

        try:
            data = await loop.run_in_executor(
                None,
                get_mc_status,
                ip
            )

            full_text = (
                f"Сервер: <code>MyAngelFujiya.Ru</code> ({data['version']})\n\n"
                f"{'☑️ Онлайн' if data['online'] else '⚠️ Оффлайн'} | "                
                f"Игроков: {data['players']}"
                # f"Пинг: {data['latency']:.0f} ms"
            )

        except Exception:
            full_text = "Сервер: <code>MyAngelFujiya.Ru</code>\n\nСтатус: ⚠️ Неизвестно или оффлайн."

        await update.message.reply_text(full_text, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка при mc: {e}")

def get_mc_status(ip, port=25565):
    server = JavaServer(ip, port)
    status = server.status()

    return {
        "online": True,
        # "latency": status.latency,
        # "players": f"{status.players.online}/{status.players.max}",
        "players": f"{status.players.online}",
        "version": status.version.name
    }