from datetime import datetime, timedelta
from pathlib import Path

# только для типов, роутер сам решает, где лежит log_file и куда писать JSON
# этот модуль НИЧЕГО не сохраняет сам

# Периоды и шаг группировки для графиков
PERIODS = {
    "1h": timedelta(hours=1),
    "12h": timedelta(hours=12),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),
    "3months": timedelta(days=90),
    "year": timedelta(days=365),
    "all": None,
}

# ---------------------------- #
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ---------------------------- #

def parse_line_datetime(line):
    try:
        date_str = line.split("]")[0].lstrip("[")
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def generate_time_buckets(period, start_time, end_time):
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
        step = timedelta(days=30)
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
    now = datetime.utcnow()
    total_requests = 0
    users = {}
    chats = set()
    commands_count = {}
    user_index = 1
    command_index = 1

    if period_delta is None:
        parsed_dates = [parse_line_datetime(l) for l in lines]
        parsed_dates = [d for d in parsed_dates if d]
        start_time = min(parsed_dates) if parsed_dates else now
    else:
        start_time = now - period_delta

    end_time = now

    buckets, step = generate_time_buckets(period_name, start_time, end_time)
    user_buckets = {}

    command_map = {}

    for line in lines:
        dt = parse_line_datetime(line)
        if dt and (period_delta is None or now - dt <= period_delta):
            total_requests += 1

            # Пользователь
            user_name = None
            if "from_user=User(" in line and "first_name=" in line:
                try:
                    user_name = line.split("from_user=User(first_name='")[1].split("'")[0]
                    if user_name not in users:
                        users[user_name] = f"data_user_{user_index}"
                        user_index += 1
                except Exception:
                    pass

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

            # Команда
            if "text='/" in line:
                try:
                    cmd_full = line.split("text='")[1].split("'")[0]
                    cmd_name = cmd_full.split()[0]
                    if "@" in cmd_name:
                        cmd_name = cmd_name.split("@")[0]
                    cmd_name = cmd_name.replace(" ", "_")

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
        "user_map": users,
        "command_map": command_map,
        "chart": {
            "labels": labels,
            "data": datasets,
        }
    }
