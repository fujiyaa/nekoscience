import json
import time
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path("status/all_updates.log")  # путь к лог-файлу
OUTPUT_FILE = Path("status/static/data/bot_stats.json")  # куда сохраняем JSON

# Периоды и шаг группировки для графиков
PERIODS = {
    "1h": timedelta(hours=1),
    "12h": timedelta(hours=12),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),
    "3months": timedelta(days=90),
    "year": timedelta(days=365),
    "all": None,  # вся история
}

# Функция парсинга даты из строки лога
def parse_line_datetime(line):
    try:
        date_str = line.split("]")[0].lstrip("[")
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

# Определяем функцию для генерации графика
def generate_time_buckets(period, start_time, end_time):
    """Возвращает список временных меток и шаг для агрегации по периоду"""
    if period == "1h":
        step = timedelta(minutes=1)
    elif period in ("12h", "day"):
        step = timedelta(hours=1)
    elif period == "week":
        step = timedelta(hours=12)
    elif period == "month":
        step = timedelta(days=1)
    elif period == "3months":
        step = timedelta(weeks=1)
    elif period == "year":
        step = timedelta(days=30)  # условно месяц
    elif period == "all":
        step = timedelta(days=365)
    else:
        step = timedelta(days=1)
    
    buckets = []
    current = start_time
    while current <= end_time:
        buckets.append(current)
        current += step
    return buckets, step

def calculate_stats_and_graph(lines, period_delta, period_name):
    """Статистика сообщений по пользователям и чистых команд с маппингом"""
    now = datetime.utcnow()
    total_requests = 0
    users = {}  # user_id -> data_user_1
    chats = set()
    commands_count = {}  # команда -> counts по корзинам
    user_index = 1
    command_index = 1

    if period_delta is None:
        start_time = min([parse_line_datetime(l) for l in lines if parse_line_datetime(l)] or [now])
    else:
        start_time = now - period_delta
    end_time = now

    buckets, step = generate_time_buckets(period_name, start_time, end_time)
    user_buckets = {}

    command_map = {}  # команда -> data_command_1, data_command_2

    for line in lines:
        dt = parse_line_datetime(line)
        if dt and (period_delta is None or now - dt <= period_delta):
            total_requests += 1

            # Пользователь
            user_name = None
            if "from_user=User(" in line and "first_name=" in line:
                try:
                    # извлекаем first_name
                    user_name = line.split("from_user=User(first_name='")[1].split("'")[0]
                    if user_name not in users:
                        users[user_name] = f"data_user_{user_index}"
                        user_index += 1
                except Exception:
                    pass

            # Добавляем пользователя в корзины
            if user_name:
                if user_name not in user_buckets:
                    user_buckets[user_name] = [0 for _ in buckets]
                for i, b in enumerate(buckets):
                    if dt >= b and (i == len(buckets)-1 or dt < buckets[i+1]):
                        user_buckets[user_name][i] += 1
                        break


            # Чат
            if "chat=Chat(" in line and "id=" in line:
                try:
                    chat_id = line.split("chat=Chat(")[1].split("id=")[1].split(",")[0]
                    chats.add(chat_id)
                except Exception:
                    pass

            # Парсим команду: берём только саму команду (до пробела), нижние подчеркивания вместо пробелов
            if "text='/" in line:
                try:
                    cmd_full = line.split("text='")[1].split("'")[0]  # /nochoke@FujiyaosuBot или /music https:/...
                    cmd_name = cmd_full.split()[0]  # оставляем только команду до пробела
                    if "@" in cmd_name:               # убираем @username
                        cmd_name = cmd_name.split("@")[0]
                    cmd_name = cmd_name.replace(" ", "_")  # заменяем пробелы
                    if cmd_name not in commands_count:
                        commands_count[cmd_name] = [0 for _ in buckets]
                        command_map[cmd_name] = f"data_command_{command_index}"
                        command_index += 1
                    for i, b in enumerate(buckets):
                        if dt >= b and (i == len(buckets)-1 or dt < buckets[i+1]):
                            commands_count[cmd_name][i] += 1
                            break
                except Exception:
                    pass

    # Форматируем метки
    labels = []
    for b in buckets:
        if period_name == "1h":
            labels.append(b.strftime("%H:%M"))
        elif period_name in ("12h", "day"):
            labels.append(b.strftime("%H:%M"))
        elif period_name == "week":
            labels.append(b.strftime("%a %H:%M"))
        elif period_name in ("month", "3months"):
            labels.append(b.strftime("%d.%m"))
        elif period_name == "year":
            labels.append(b.strftime("%b %Y"))
        elif period_name == "all":
            labels.append(b.strftime("%Y"))

    # Формируем данные для Chart.js
    datasets = {v: user_buckets[k] for k, v in users.items()}
    datasets.update({v: commands_count[k] for k, v in command_map.items()})

    data_total = [0 for _ in buckets]
    for i in range(len(buckets)):
        for user_vals in user_buckets.values():
            data_total[i] += user_vals[i]
        for cmd_vals in commands_count.values():
            data_total[i] += cmd_vals[i]
    datasets["data_total"] = data_total
    
    return {
        "total_requests": total_requests,
        "users": len(users),
        "chats": len(chats),
        "commands": len(commands_count),
        "user_map": users,        # отображение user_id -> data_user_N
        "command_map": command_map,  # отображение команды -> data_command_N
        "chart": {
            "labels": labels,
            "data": datasets
        }
    }


def main():
    while True:
        if LOG_FILE.exists():
            with LOG_FILE.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            data = {}
            for period_name, delta in PERIODS.items():
                data[period_name] = calculate_stats_and_graph(lines, delta, period_name)

            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with OUTPUT_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"[{datetime.utcnow()}] Статистика обновлена")
        else:
            print(f"[{datetime.utcnow()}] Лог-файл не найден: {LOG_FILE}")

        time.sleep(60)

if __name__ == "__main__":
    main()