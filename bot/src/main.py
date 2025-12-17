

# остальные модули импортируются внутри конфига, такие как longtext.py
from config import *
import localapi, auth

import temp            

blacklist = temp.load_text_list(BLACKLIST_FILE, as_set=True)

log_queue = asyncio.Queue()
logger_task = None
logger_lock = asyncio.Lock()

async def logger_worker():
    while True:
        update = await log_queue.get()
        if update is None:
            break

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{now}] Update in chat {update.effective_chat.id}, "
                f"topic {getattr(update.effective_message, 'message_thread_id', None)}: {update}\n")

        with open(ALL_UPDATES_LOG, "a", encoding="utf-8") as f:
            f.write(line)

        log_queue.task_done()

async def ensure_logger_started():
    global logger_task
    async with logger_lock:
        if logger_task is None:
            logger_task = asyncio.create_task(logger_worker())

async def log_all_update(update):
    await ensure_logger_started()
    await log_queue.put(update)

async def stop_logger():
    await log_queue.put(None)
    await logger_task

def log_deleted_message(user, message_text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DELETED_MESSAGES_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Удалено сообщение от пользователя {user}:\n{message_text}\n\n")

def format_osu_date(date_str: str, today: bool = True) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += timedelta(hours=3)
    if today:
        return f'{dt.strftime("%H:%M")}MSK'
    else:
        return dt.strftime("%d.%m.%Y")
def seconds_to_hhmmss(seconds: float) -> str:
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
def reset_remove_timer(bot, chat_id, msg_id, delay=30, cleanup=None):    
    if msg_id in remove_tasks:
        remove_tasks[msg_id].cancel()

    async def delayed():
        await asyncio.sleep(delay)
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=None
            )
        except Exception:
            pass
        finally:
            remove_tasks.pop(msg_id, None)
            if cleanup:
                cleanup()

    task = asyncio.create_task(delayed())
    remove_tasks[msg_id] = task
def apply_mods_to_stats(bpm, ar, od, cs, hp, speed_multiplier=1.0, hr=False, ez=False):
    bpm = Decimal(str(bpm))
    ar = Decimal(str(ar))
    od = Decimal(str(od))
    cs = Decimal(str(cs))
    hp = Decimal(str(hp))
    speed_multiplier = Decimal(str(speed_multiplier))

    if ez:
        ar *= Decimal('0.5')
        od *= Decimal('0.5')
        cs *= Decimal('0.5')
        hp *= Decimal('0.5')      

    if hr:
        ar = min(ar * Decimal('1.4'), Decimal('10'))
        od = min(od * Decimal('1.4'), Decimal('10'))
        cs = min(cs * Decimal('1.3'), Decimal('10'))
        hp = min(hp * Decimal('1.4'), Decimal('10'))

    if speed_multiplier != 1:
        if ar < 5:
            ar_ms = Decimal('1800') - Decimal('120') * ar
        else:
            ar_ms = Decimal('1200') - Decimal('150') * (ar - 5)
        ar_ms /= speed_multiplier
        if ar_ms > 1200:
            ar = (Decimal('1800') - ar_ms) / Decimal('120')
        else:
            ar = Decimal('5') + (Decimal('1200') - ar_ms) / Decimal('150')

        hit300 = Decimal('80') - Decimal('6') * od
        hit100 = Decimal('140') - Decimal('8') * od
        hit50  = Decimal('200') - Decimal('10') * od

        hit300 /= speed_multiplier
        hit100  /= speed_multiplier
        hit50   /= speed_multiplier

        od = (Decimal('80') - hit300) / Decimal('6')

        bpm *= speed_multiplier

    def osu_round(val):
        return float(val.quantize(Decimal('0.01'), rounding='ROUND_HALF_UP'))

    bpm_r = osu_round(bpm)
    ar_r  = osu_round(ar)
    od_r  = osu_round(od)
    cs_r  = osu_round(cs)
    hp_r  = osu_round(hp)

    return bpm_r, ar_r, od_r, cs_r, hp_r
def normalize_plus(text: str) -> str:
    if isinstance(text, list):
        text = "".join(text) 
    clean_text = text.replace('+', '').strip()
    return f"+{clean_text}" if clean_text else ""
def normalize_no_plus(text: str) -> str:
    if isinstance(text, list):
        text = "".join(text) 
    clean_text = text.replace('+', '').strip()
    return f"{clean_text}" if clean_text else ""
def format_mods(mod_list):
    return "".join(mod_list) if mod_list else "NM"
def format_blocks_percent(counter, total, per_row):
    items_raw = [(k, f"{round(v / total * 100)}%") for k, v in counter.most_common()]
    max_key_len = max(len(k) for k, _ in items_raw)
    max_val_len = max(len(val) for _, val in items_raw)

    if max_key_len > 4:
        per_row = max(1, per_row - 1)

    items = [
        f"<code>{k}:{' ' * (max_key_len - len(k) + 1)}{val.rjust(max_val_len)}</code>"
        for k, val in items_raw
    ]
    lines = [" • ".join(items[i:i+per_row]) for i in range(0, len(items), per_row)]
    return "\n".join(lines)
def format_blocks_pp(data_dict, per_row):
    items_raw = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    max_key_len = max(len(k) for k, _ in items_raw)
    max_val_len = max(len(f"{round(v,1)}") for _, v in items_raw)

    if max_key_len > 4:
        per_row = max(1, per_row - 1)

    items = [
        f"<code>{k}:{' ' * (max_key_len - len(k) + 1)}{str(round(v, 1)).rjust(max_val_len)}</code>"
        for k, v in items_raw
    ]
    lines = [" • ".join(items[i:i+per_row]) for i in range(0, len(items), per_row)]
    return "\n".join(lines)
def country_code_to_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return ""
    
    return "".join(
        chr(0x1F1E6 + ord(char.upper()) - ord('A'))
        for char in country_code
    )
def format_stats(user, best_pp):
    stats = user["statistics"]
    level = float(f"{stats['level']['current']}.{stats['level']['progress']}")
    hours = stats["play_time"] // 3600
    medals = len(user["user_achievements"])
    ss_count = stats.get("grade_counts", {}).get("ss", 0)
    s_count = stats.get("grade_counts", {}).get("s", 0)
    a_count = stats.get("grade_counts", {}).get("a", 0)
    monthly = user.get('monthly_playcounts', [])

    if monthly:
        max_count = max(item['count'] for item in monthly)
    else:
        max_count = 0  # если список пустой
    
    if best_pp:
        pp_values = [item['pp'] for item in best_pp]
        pp_diff = max(pp_values) - min(pp_values)
        pp_avg_all = sum(pp_values) / len(pp_values)
    else:
        pp_values = []
        pp_diff = 0
        pp_avg_all = 0

    # 2. Среднее PP по месяцам
    # Группируем по месяцу
    pp_by_month = defaultdict(list)
    for item in best_pp:
        # допустим, есть ключ 'date' или можно использовать индекс для примера
        month = item.get('date', str(best_pp.index(item)))[:7]  # YYYY-MM
        pp_by_month[month].append(item['pp'])


    # 3. Средний count в месяц
    monthly_counts = user.get('monthly_playcounts', [])
    if monthly_counts:
        avg_count_per_month = sum(item['count'] for item in monthly_counts) / len(monthly_counts)
    else:
        avg_count_per_month = 0

    total_pp = stats.get("pp", 0)
    num_months = len(user.get('monthly_playcounts', []))
    avg_pp_per_month = total_pp / num_months if num_months > 0 else 0

    hpp = round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)

    return {
        "name": user["username"],
        "rank": stats.get("global_rank") or 0,
        "peak_rank": user["rank_highest"]["rank"] if user.get("rank_highest") else 0,
        "pp": stats.get("pp", 0),
        "acc": stats.get("hit_accuracy", 0),
        "level": level,
        "hours": hours,
        "playcount": stats.get("play_count", 0),
        "avg_count_per_month": avg_count_per_month,
        "ranked_score": user['statistics']['ranked_score'],
        "ranked_score": stats.get("ranked_score", 0),
        "total_score": stats.get("total_score", 0),
        "total_hits": stats.get("total_hits", 0),
        "ss": ss_count,
        "s": s_count,
        "a": a_count,
        "max_combo": stats.get("maximum_combo", 0),
        "medals": medals,
        "join_date": user["join_date"].split("T")[0],
        "replays": stats.get("replays_watched_by_others", 0),
        "top1_pp": best_pp[0]["pp"] if best_pp else 0,
        "pp_avg_all": pp_avg_all,
        "avg_pp_per_month": avg_pp_per_month,
        "pp_diff": pp_diff,
        "max_count":max_count,
        "followers":user['follower_count'],
        "mapping":user['mapping_follower_count'],
        "maps":user['beatmap_playcounts_count'],
        "posts":user['post_count'],
        "hpp":hpp,
    }
def row(val1, mid, val2, higher_is_better=True, suffix="", preffix: str = None, fmt="{:,}", is_date=False):
    def format_val(v):
        if is_date:
            return str(v)  # для даты просто оставляем строку
        try:
            n = float(v)
        except:
            return str(v)

        if n.is_integer():
            return f"{int(n):,}{suffix}"
        else:
            return fmt.format(n) + suffix

    left, right = format_val(val1), format_val(val2)

    # Сравнение
    try:
        if is_date:
            n1 = datetime.fromisoformat(val1)
            n2 = datetime.fromisoformat(val2)
        else:
            n1 = float(val1)
            n2 = float(val2)

        if preffix:
            left = f"{preffix}{left}"
            right = f"{preffix}{right}"

        if n1 != n2:
            better_left = (n1 > n2) if higher_is_better else (n1 < n2)
            if better_left:
                left = f"{left} <"
                right = f"  {right}"
            else:
                left = f"{left}  "
                right = f"> {right}"
        else:
            left = f"{left}  "
            right = f"  {right}"
    except:
        pass

    return f"{left:>{COL1}}| {mid:^{COLMID}} |{right:<{COL2}}"
def make_header(name1, name2):
    header = f"{name1:>{COL1}} | {'osu!':^{COLMID}} | {name2:<{COL2}}"
    sep = f"{'-'*COL1}+{'-'*(COLMID+2)}-{'-'*COL2}"
    return header, sep
def calculate_weighted_pp(best_pp, bonus_pp:float = 413.89):
    total_pp = 0.0
    for entry in best_pp:
        pp = float(entry['pp'])
        weight = entry.get('weight_percent', 100) / 100
        total_pp += pp * weight
    return (total_pp+bonus_pp)
def insert_pp(data, new_pp, new_mods=None, new_mapper=''):
    if new_mods is None:
        new_mods = []

    saved_weights = [entry.get('weight_percent') for entry in data]

    if float(new_pp) < float(data[-1]['pp']):
        return None

    position = 0
    while position < len(data) and float(new_pp) < float(data[position]['pp']):
        position += 1

    new_entry = {
        'pp': float(new_pp),
        'mods': new_mods,
        'mapper': new_mapper
    }
    data.insert(position, new_entry)

    # Обрезаем до 100 элементов
    if len(data) > 100:
        data = data[:100]

    # Восстанавливаем старые weight_percent для существующих элементов
    for i, weight in enumerate(saved_weights[:len(data)]):
        data[i]['weight_percent'] = weight

    return position, data

async def beatmap(map_id: int) -> tuple[str | None, dict]:
    """
    Скачивает карту (если нет или устарела) и возвращает:
    (путь_к_файлу, dict с base-значениями HP/CS/OD/AR)
    """
    path_to_map = os.path.join(BEATMAPS_DIR, f"{map_id}.osu")

    # словарь с дефолтами
    base_values = {
        "hp": None,
        "cs": None,
        "od": None,
        "ar": None
    }

    def parse_values(path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("HPDrainRate:"):
                        base_values["hp"] = float(line.split(":")[1].strip())
                    elif line.startswith("CircleSize:"):
                        base_values["cs"] = float(line.split(":")[1].strip())
                    elif line.startswith("OverallDifficulty:"):
                        base_values["od"] = float(line.split(":")[1].strip())
                    elif line.startswith("ApproachRate:"):
                        base_values["ar"] = float(line.split(":")[1].strip())
        except Exception as e:
            print(f"⚠ Ошибка при парсинге .osu {map_id}: {e}")

    if os.path.exists(path_to_map):
        file_age = time.time() - os.path.getmtime(path_to_map)
        if file_age < CACHE_TTL:
            parse_values(path_to_map)
            return path_to_map, base_values
        else:
            os.remove(path_to_map)

    base_url = 'https://osu.ppy.sh/osu'
    try:
        response = requests.get(f'{base_url}/{map_id}', timeout=3)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при скачивании карты {map_id}: {e}")
        return None, base_values

    with open(path_to_map, 'w', encoding="utf-8") as f:
        f.write(response.text)

    parse_values(path_to_map)
    return path_to_map, base_values
async def build_beatmaps_text(caller_id: int) -> tuple[str, InlineKeyboardMarkup]:
    queue_count = 0
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            queue_count = sum(1 for _ in f)

    users_states = []
    done_count = 0

    if os.path.exists(GROUPS_DIR):
        verified_all = await auth.get_all_osu_verified()  

        for fname in os.listdir(GROUPS_DIR):
            if "." in fname:
                uid, status = fname.split(".", 1)
                saved_data = verified_all.get(uid)
                saved_name = saved_data["osu_username"] if saved_data else "неизвестно"

                if status == "todo":
                    users_states.append((saved_name, "не готово"))
                elif status == "done":
                    done_count += 1

    # таблица
    max_name_len = max((len(name) for name, _ in users_states), default=4)
    header = f"{'Имя'.ljust(max_name_len)} | Статус"
    table_lines = [f"`{header}`"]
    for name, status in users_states:
        line = f"{name.ljust(max_name_len)} | {status}"
        table_lines.append(f"`{line}`")

    if users_states:
        table_text = "\n".join(table_lines)
    else:
        table_text = "`нет никого в очереди!`"

    if done_count > 0:
        table_text += f"\n+{done_count} уже готовых.."


    # пример времени
    seconds_todo = ""
    if queue_count > 0:
        total_seconds = queue_count * URL_SCAN_TIMEOUT
        if total_seconds < 60:
            seconds_todo = f", примерно *{total_seconds}* секунд осталось"
        else:
            minutes = total_seconds // 60
            seconds_todo = f", примерно *{minutes}* минут осталось"

    msg = (
        f"📄 Карт в очереди: *{queue_count}* {seconds_todo}\n\n"
        f"{table_text}"
        f"\n\n💧 Занимает время, так что просто подожди немного. Время - с запасом, будет готово немного раньше. Считается в порядке очереди (добавляешься при идущем расчете, не влияет на время ожидания других). Чтобы добавить себя, нажми кнопку со звездочкой."
    )

    # клавиатура
    keyboard = [
        [
            InlineKeyboardButton("🔄 Обновить", callback_data=f"beatmaps_refresh:{caller_id}"),
            InlineKeyboardButton("⭐️ Посчитать меня", callback_data=f"beatmaps_count_me:{caller_id}"),
        ],
        [
            InlineKeyboardButton("посмотреть статистику карт из...", callback_data=f"beatmaps_refresh:{caller_id}"),
        ],
        [
            InlineKeyboardButton("📊 200 карт", callback_data=f"beatmaps_stats_200:{caller_id}"),
            InlineKeyboardButton("🔹 top-100 pp", callback_data=f"beatmaps_stats_1_100:{caller_id}"),
            InlineKeyboardButton("🔸 most played", callback_data=f"beatmaps_stats_101_200:{caller_id}"),            
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return msg, reply_markup
def mark_group_progress():
    for fname in os.listdir(GROUPS_DIR):
        if not fname.endswith(".todo"):
            continue

        group_id = fname.split(".")[0]
        todo_path = os.path.join(GROUPS_DIR, fname)
        done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

        if os.path.exists(done_path):
            continue

        with open(todo_path, "r", encoding="utf-8") as f:
            targets = [line.strip() for line in f if line.strip()]

        all_ready = all(os.path.exists(path) for path in targets)

        if all_ready:
            os.rename(todo_path, done_path) 
            print(f"✅ Группа {group_id} завершена!")
 
def get_stats_cache_path(beatmap_id):
    return f"{STATS_BEATMAPS}/{beatmap_id}.json"
def get_profile_keyboard(current: str):
    """
    current: 'profile' или 'card'
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 Профиль", callback_data="profile" if current != "profile" else "noop"
            ),
            
            InlineKeyboardButton(
                "🖼 Карточка", callback_data="card" if current != "card" else "noop"
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         "статистика по топ-100 рекордам:", callback_data="noop"
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         "🗂 Карты", callback_data="profile_beatmaps" if current != "profile_beatmaps" else "noop"
        #     ),
        #     InlineKeyboardButton(
        #         "👥 Мапперы", callback_data="profile_mappers" if current != "profile_mappers" else "noop"
        #     ),            
        #     InlineKeyboardButton(
        #         "🫧 Моды", callback_data="profile_mods" if current != "profile_mods" else "noop"
        #     )
        # ]
    ])
def get_mods_info(mods):
    """
    mods может быть:
    - строка: "HR+DT"
    - список: ["HR", "DT"]
    - список объектов: [{'acronym': 'DT'}, {'acronym': 'HR'}]
    - или содержать кастомные надписи: "DT (1.83X)"
    """
    mods_acronyms = []
    speed_multiplier = 1.0
    hr = False
    ez = False

    if mods:
        if isinstance(mods, str):
            mods_acronyms = mods.upper().split('+')
        elif isinstance(mods, list):
            mods_acronyms = [
                m['acronym'].upper() if isinstance(m, dict) else str(m).upper() 
                for m in mods
            ]

    # Проверка на HR, EZ
    hr = "HR" in mods_acronyms
    ez = "EZ" in mods_acronyms

    # Проверка на DT / NC / HT и кастомные мультипликаторы
    for mod in mods_acronyms:
        # Ищем кастомный множитель в формате "(X.XXX)"
        match = re.search(r'\(([\d.]+)X\)', mod)
        if match:
            try:
                speed_multiplier = float(match.group(1))
            except ValueError:
                pass  # оставляем предыдущий speed_multiplier
        else:
            # Стандартные множители
            if "DT" in mod or "NC" in mod:
                speed_multiplier = 1.5
            elif "HT" in mod:
                speed_multiplier = 0.75

    return speed_multiplier, hr, ez

async def read_cooldowns():
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    async with aiofiles.open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        try:
            data = await f.read()
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
async def write_cooldowns(data):
    async with aiofiles.open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))
async def check_user_cooldown(command_name: str, user_id: str, cooldown_seconds: int, 
                              update=None, context=None, warn_text=None):
    now = datetime.now(timezone.utc).isoformat()
    cooldown = timedelta(seconds=cooldown_seconds)

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})

    last_used_str = user_cooldowns.get(user_id)
    if last_used_str:
        last_used = datetime.fromisoformat(last_used_str)
        if datetime.now(timezone.utc) - last_used < cooldown:
            if not warn_text is None:
                if update and context:
                    try:
                        await update.message.delete()
                    except Exception:
                        pass
                
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=warn_text,
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 3))
            return False

    user_cooldowns[user_id] = now
    data[command_name] = user_cooldowns
    await write_cooldowns(data)
    return True
async def is_on_cooldown(command_name: str, cooldown_seconds: int) -> bool:
    bot_id = str(727)
    cooldown = timedelta(seconds=cooldown_seconds)

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})
    
    last_used_str = user_cooldowns.get(bot_id)
    if last_used_str:
        last_used = datetime.fromisoformat(last_used_str)
        if datetime.now(timezone.utc) - last_used < cooldown:
            return True
    return False

async def update_cooldown(command_name: str):
    bot_id = str(727)
    now = datetime.now(timezone.utc).isoformat()

    data = await read_cooldowns()
    user_cooldowns = data.get(command_name, {})
    
    user_cooldowns[bot_id] = now
    data[command_name] = user_cooldowns
    await write_cooldowns(data)
async def delete_message_after_delay(context, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
async def delete_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, delay: int = 5):
    if not update.message:
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении пользовательского сообщения: {e}")

#retries
async def safe_query_answer(query, text=None, show_alert=True, retries=2, delay=1):
    attempt = 0
    while attempt <= retries:
        try:
            if text is not None:
                await query.answer(text, show_alert=show_alert)
            else:
                await query.answer()
            return
        except Exception as e:
            attempt += 1
            if attempt > retries:
                print(f"❌ Не удалось отправить ответ: {e}")
                return
            await asyncio.sleep(delay)  # ждем перед следующей попыткой
async def safe_edit_message(message, text, parse_mode=None, reply_markup=None):
    try:       
        if message and (message.text or message.caption):
            return await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            return await message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        print(f"safe_edit_message failed: {e}")
        return await message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup) 
async def fetch_with_timeout(session, url, headers=None, timeout_sec=10):
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        async with session.get(url, headers=headers, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request to {url} failed: {e}")
        return None
async def safe_send_message(update: Update, text: str, parse_mode=None):
    for _ in range(5):
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")
            await asyncio.sleep(1)
    logging.error("Не удалось отправить сообщение после 5 попыток.")
    return None
async def try_send(coro_func, *args, retries=3, delay=1, **kwargs):
    for attempt in range(retries):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                print(f"Failed after {retries} attempts: {e}")
                return None
async def try_request(coro, retries=3, delay=1, *args, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            return await coro(*args, **kwargs)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == retries:
                print(f"Последняя попытка не удалась: {e}")
                raise
            print(f"Сетевая ошибка: {e}, попытка {attempt}/{retries}, повтор через {delay}s...")
            await asyncio.sleep(delay)

#api TODO cleaning
async def get_user_profile(username: str, token: str = None) -> dict | None:
    if token is None:
        token = await get_osu_token()
    url = f"https://osu.ppy.sh/api/v2/users/{username}/osu"
    headers = {"Authorization": f"Bearer {token}"}
    print('🔻 API request (get_user_profile)')
    async with aiohttp.ClientSession() as session:
        data = await fetch_with_timeout(session, url, headers)
        return data               
async def get_best_pp_by_username(username: str, token: str = None) -> float | None:
    if token is None:
        token = await get_osu_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        user_url = f"https://osu.ppy.sh/api/v2/users/{username}/osu"
        user_data = await fetch_with_timeout(session, user_url, headers)
        if not user_data:
            print(f"User {username} not found or request failed")
            return None
        user_id = user_data["id"]

        best_scores_url = f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/best?mode=osu&limit=1"
        best_scores = await fetch_with_timeout(session, best_scores_url, headers)
        if not best_scores:
            print("Failed to get best scores or no scores found")
            return None

        best_pp = best_scores[0].get("pp")
        return str(best_pp)
async def get_top_100_scores(username: str, token: str = None, user_id: str = None, limit: int = 100, plain: bool = False) -> list[dict] | None:
    if token is None:
        token = await try_request(get_osu_token, retries=3, delay=1)

    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        if user_id is None:
            user_url = f"https://osu.ppy.sh/api/v2/users/{username}/osu"
            print('🔻 API request (get_top_100_scores 1/2)')
            user_data = await try_request(fetch_with_timeout, retries=3, delay=1, session=session, url=user_url, headers=headers)
            if not user_data or "id" not in user_data:
                print(f"User {username} not found or request failed")
                return None
            user_id = user_data["id"]

        best_scores_url = f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/best?mode=osu&limit={limit}"
        print('🔻 API request (get_top_100_scores 2/2)')
        best_scores = await try_request(fetch_with_timeout, retries=3, delay=1, session=session, url=best_scores_url, headers=headers)
        if not best_scores:
            print("Failed to get best scores or no scores found")
            return None

        if plain: return best_scores
        
        results = []
        for score in best_scores:
            mapper_name = score.get("beatmapset", {}).get("creator", "Unknown")
            version = score.get("beatmap", {}).get("version", "")
            if "'" in version:
                mapper_name = version.split("'", 1)[0].strip()
            lazer = True
            stable = is_legacy_score(score)
            if stable:
                lazer = False

            results.append({
                'beatmap_url': score.get("beatmap", {}).get("url"),
                "pp": score.get("pp"),
                "weight_percent": score.get("weight", {}).get("percentage"),
                "mods": score.get("mods", []),
                "mapper": mapper_name,
                "OD": score.get('beatmap', {}).get('accuracy'),
                "AR": score.get('beatmap', {}).get('ar'),
                "CS": score.get('beatmap', {}).get('cs'),
                "HP": score.get('beatmap', {}).get('drain'),
                "bpm": score.get('beatmap', {}).get('bpm'),                
                "length": score.get('beatmap', {}).get('hit_length'),
                "stars": score.get('beatmap', {}).get('difficulty_rating'),
                "plays": score.get('beatmap', {}).get('passcount'),
                "passes": score.get('beatmap', {}).get('playcount'),
                "passes": score.get('beatmap', {}).get('playcount'),
                "accuracy": score.get('accuracy'),
                "misses": score.get('statistics', {}).get('count_miss'),
                "combo": score.get('max_combo'),
                "beatmap_id": score.get('beatmap', {}).get('id'),
                "score_stats": score.get('statistics', {}),
                "version": score.get('beatmap', {}).get('version'),
                "title": score.get('beatmapset', {}).get('title'),
                "lazer": lazer,
            })

        return results    
async def get_most_played(username: str, token: str = None) -> list[dict] | None:
    if token is None:
        token = await get_osu_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        user_url = f"https://osu.ppy.sh/api/v2/users/{username}/osu"
        user_data = await fetch_with_timeout(session, user_url, headers)
        if not user_data:
            print(f"User {username} not found or request failed")
            return None
        user_id = user_data["id"]

        most_played_url = f"https://osu.ppy.sh/api/v2/users/{user_id}/beatmapsets/most_played?limit=100"
        most_played = await fetch_with_timeout(session, most_played_url, headers)
        if not most_played:
            print("Failed to get most_played or no most_played found")
            return None

        results = []
        for map in most_played:
            mapset_id = map['beatmap']['beatmapset_id']
            map_id = map['beatmap']['id']
            mode = map['beatmap']['mode']

            results.append({
                'beatmap_url':f"https://osu.ppy.sh/beatmapsets/{mapset_id}#{mode}/{map_id}",
            })

        return results
_cached_token = None
_token_expiry = 0
async def get_osu_token(timeout_sec: int = 10):
    global _cached_token, _token_expiry
    now = time.time()

    if _cached_token and now < _token_expiry:
        return _cached_token

    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        print('🔻 API request (token)')
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://osu.ppy.sh/oauth/token",
                json={
                    "client_id": OSU_CLIENT_ID,
                    "client_secret": OSU_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                    "scope": "public"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _cached_token = data.get("access_token")
                    expires_in = data.get("expires_in", 60) 
                    _token_expiry = now + expires_in - 5  
                    return _cached_token
                else:
                    print(f"Token request failed with status {resp.status}")
                    return None
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Token request error: {e}")
        return None
async def get_beatmap(beatmap_id: int, token: str, timeout_sec: int = 10):
    url = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        print('🔻 API request (token)')
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for beatmap_id '{beatmap_id}' failed: {e}")
        return None
async def get_user_id(username: str, token: str = None, timeout_sec: int = 10):
    user_cache = temp.load_json(OSU_ID_CACHE_FILE, {})

    if username in user_cache:
        return user_cache[username]

    if token is None:
        token = await get_osu_token()
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        print('🔻 API request (get_user_id)')
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://osu.ppy.sh/api/v2/users/{username}/osu",
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                user_id = data.get("id")
                if user_id:
                    user_cache[username] = user_id
                    temp.save_json(OSU_ID_CACHE_FILE, user_cache)
                return user_id
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for user_id '{username}' failed: {e}")
        return None
async def get_osu_user_additional_data(user_id: str, mode: str, token: str = None, timeout_sec: int = 10):
    if token is None:
        token = await get_osu_token()

    url = f"https://osu.ppy.sh/api/v2/users/{user_id}/{mode}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        print('🔻 API request (get_osu_user_additional_data)')
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    print("Error:", resp.status)
                    return None
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for user_pp failed: {e}")
        return None
async def get_score_page(session, user_id: str, score_id: str, no_check:bool = False) -> dict | None:  
    url = f"https://osu.ppy.sh/scores/{score_id}"
    try:
        print(f'🔻 lxml request ({score_id})')
        async with semaphore:
            async with session.get(url) as resp:
                if resp.status == 200:
                    html_text = await resp.text()
                    tree = lxml.html.fromstring(html_text)
                    script = tree.xpath('//script[@id="json-show"]/text()')
                    if script:
                        try:
                            data = json.loads(script[0])
                            if not no_check:
                                if not str(data['user_id']) == str(user_id):
                                    return None
                            # Сохраняем в файл
                            # cached_entry = {"raw": data, "processed": {}, "ready": False}
                            # save_score_file(score_id, cached_entry)

                            return data
                        except json.JSONDecodeError:
                            print(f"⚠ Ошибка JSON в score {score_id}")
                            return None
                else:
                    print(f"⚠ Ошибка HTTP {resp.status} для score {score_id}")
                    return None
    except Exception as e:
        print(f"⚠ Ошибка при загрузке score {score_id}: {e}")

    return None
async def get_user_scores(username: str, token: str, timeout_sec: int = 10, limit: int = 25):
    user_id = await get_user_id(username, token)
    if not user_id:
        return None

    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/recent?limit={limit}",
                headers={"Authorization": f"Bearer {token}"}
            ) as resp:
                if resp.status != 200:
                    print(f"⚠ Ошибка HTTP {resp.status} при получении скор")
                    return None
                data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"⚠ Ошибка запроса get_user_scores: {e}")
            return None

    if not data:
        return []

    for score in data:
        if score.get("id", 0) == 0:
            created_at = score.get("created_at", "unknown_time")
            safe_time = re.sub(r'[^\w\-]', '_', created_at)
            score["id"] = f"{user_id}_{safe_time}"    

    additional_data = await get_osu_user_additional_data(user_id, "osu", token)

    results = []
    async with aiohttp.ClientSession() as session:
        for idx, s in enumerate(data):
            score_id = str(s["id"])
            cached_entry = load_score_file(score_id)
            if not cached_entry:
                cached_entry = {"raw": s, "processed": {}, "ready": False}
                save_score_file(score_id, cached_entry)

            
                final_score = await process_score(cached_entry["raw"], additional_data)

                cached_entry["raw"] = final_score
                cached_entry["ready"] = False
                save_score_file(score_id, cached_entry)
                if idx == 0 and not cached_entry.get("ready"):
                    await enrich_score_lazer(session, str(s['user']['id']), score_id)                      
                    cached_entry = load_score_file(score_id)   
                    final_score = cached_entry["raw"]                
            else:
                final_score = cached_entry["raw"]
                
            results.append(final_score)
    return results

#rs cmd TODO
async def start_rs(update, context, is_button_press=False):
    await log_all_update(update)
    asyncio.create_task(rs(update, context, is_button_press))
async def rs(update: Update, context: ContextTypes.DEFAULT_TYPE, is_button_press=False):
    user_id = str(update.effective_user.id)
    can_run = await check_user_cooldown(
        command_name="rs",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_RS_COMMAND,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_RS_COMMAND} секунд"
    )
    if not can_run:
        return

    max_attempts = 3
    for _ in range(max_attempts):
        try:
            if not is_button_press:          
                saved_name = await auth.check_osu_verified(str(update.effective_user.id))
                username = context.args[0] if context.args else saved_name
                if not username:
                    await safe_send_message(update, "⚠ Не указан ник", parse_mode="Markdown")
                    return
            else:
                msg = update.callback_query.message
                session_data = user_sessions.get(msg.message_id)
                if not session_data:
                    await update.callback_query.answer("⚠️ Сессия устарела", show_alert=True)
                    return
                username = session_data["username"]
                saved_name = session_data.get("saved_name", "нет")

            if not is_button_press:
                loading_msg = await try_send(update.message.reply_text, "`загрузка...`", parse_mode="Markdown")

                token = await get_osu_token()
                scores = await get_user_scores(username, token, limit=100)
                if not scores:
                    await safe_send_message(update, "❌ Нет последних игр", parse_mode="Markdown")
                    return

                score = scores[0]
               
                local_session = {
                    "scores": scores,
                    "index": 0,
                    "user_id": user_id,
                    "username": username,
                    "saved_name": saved_name
                }

                msg = await try_send(send_score, update, score, user_id, local_session, message_id=0)
                await loading_msg.delete()

                message_id = msg.message_id
                user_sessions[message_id] = local_session

                asyncio.create_task(cache_remaining_scores(str(scores[0]['user']['id']), scores, username))

            else:
                msg = update.callback_query.message
                session_data = user_sessions.get(msg.message_id)
                scores = session_data["scores"]
                index = session_data["index"]
                score = scores[index]
                message_id = msg.message_id
                await send_score(update, score, session_data["user_id"], session_data, message_id, query=update.callback_query)

            session = user_sessions[message_id]
            index = session["index"]
            total = len(session["scores"])

            buttons = [
                InlineKeyboardButton("⬅️", callback_data=f"rs_prev_{message_id}" if index > 0 else "rs_disabled"),
                InlineKeyboardButton(f"{index+1}/{total}", callback_data="rs_disabled"),
                InlineKeyboardButton("➡️", callback_data=f"rs_next_{message_id}" if index < total - 1 else "rs_disabled")
            ]

            try:
                keyboard = InlineKeyboardMarkup([buttons])
                await try_send(msg.edit_reply_markup, reply_markup=keyboard)
            except:
                print('keyboard not edited (rs)')

            reset_remove_timer(
                context.bot,
                msg.chat.id,
                msg.message_id,
                RS_BUTTONS_TIMEOUT,
                cleanup=lambda: user_sessions.pop(msg.message_id, None)
            )
            return

        except Exception:
            traceback.print_exc()

async def send_score( update: Update, score: dict, user_id: str,  session: dict,  message_id: int, query=None,  show_buttons=True, img_path=None, is_recent=True):
    s =  temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)  
    img_path, caption = await process_score_and_image(score, image_todo_flag=rs_bg_render, is_recent=is_recent)

    link_preview = LinkPreviewOptions(
        url=score.get('card2x_url'),
        is_disabled=False,
        prefer_small_media=False,
        prefer_large_media=True,
        show_above_text=True
    )

    try:
        if query:
            if img_path:
                with open(img_path, "rb") as f:
                    bio = BytesIO(f.read())
                media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
                await query.edit_message_media(media=media)
            else:
                await query.edit_message_text(
                    text=caption,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                )
        else:
            if img_path:
                return await update.message.reply_photo(
                    photo=open(img_path, "rb"),
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                return await update.message.reply_text(
                    caption,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                )
    except Exception:
        traceback.print_exc()
async def process_score(score, additional_data):
    raw = score

    beatmap = raw.get("beatmap", {})
    beatmapset = raw.get("beatmapset", {})

    score_id = str(raw.get("id"))
    score_url = f"https://osu.ppy.sh/scores/{score_id}" if score_id else None
    lazer = raw.get("lazer", False)
    da_active = any(mod for mod in (raw.get("mods", []) or []) if mod == "DA")
    speed_multiplier = raw.get("speed_multiplier")
    custom_values = raw.get("DA_values", {})
    accuracy = raw.get("accuracy", score.get("accuracy"))
    mods_text = raw.get("mods", "+".join(score.get("mods", [])) if score.get("mods") else "NM")

    if speed_multiplier:
        mods_text += f" ({speed_multiplier}x)"
    if da_active:
        if mods_text == "NM":
            mods_text = "+DA"
        else:
            mods_text += "+DA"

    return {
        "score": raw.get("score"),
        "pp": raw.get("pp") or "N/A",
        "rank": raw.get("rank"),
        "mods": mods_text,
        "date": raw.get("created_at") or raw.get("ended_at"),
        "card2x_url": beatmapset.get('covers', {}).get('card@2x'),
        "beatmap": beatmap,
        "beatmapset": beatmapset,
        "beatmap_full": f"{beatmapset.get('artist', '')} - {beatmapset.get('title', '')} [{beatmap.get('version', '')}]",
        "accuracy": accuracy,
        "max_combo": raw.get("max_combo"),
        "count_miss": raw.get("statistics", {}).get("count_miss") or raw.get("statistics", {}).get("miss") or 0,
        "bpm": beatmap.get("bpm"),
        "url": beatmap.get("url"),
        "hit_length": beatmap.get("hit_length"),
        "cs": beatmap.get("cs"),
        "ar": beatmap.get("ar"),
        "od": beatmap.get("accuracy"),
        "hp": beatmap.get("drain"),
        "mapper": beatmapset.get("creator"),
        "status": beatmap.get("status"),
        "score_url": score_url,
        "speed_multiplier": speed_multiplier,
        "user": raw.get("user"),
        "username": additional_data['username'],
        "total_pp": additional_data['statistics']['pp'],
        "country_rank": additional_data['statistics']['country_rank'],
        "global_rank": additional_data['statistics']['global_rank'],
        "country_code": additional_data['country_code'],
        "DA_values": custom_values,
        "lazer": lazer,
        "score_stats": raw.get("statistics", {}),
        "id": raw.get("id")
    }



async def process_score_and_image(score, image_todo_flag = False, is_recent=True):       
    mods_str = score.get("mods", "")
    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

    path, base_values = await beatmap(score['beatmap']['id'])

    base_values["ar"] = score.get("ar", 5) if base_values.get("ar") is None else base_values["ar"]
    
    base_ar = score.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = score.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = score.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = score.get("DA_values", {}).get("drain_rate", base_values["hp"])

    score_stats = score.get("score_stats", score.get("statistics"))
    misses = score.get('count_miss', score.get("statistics", {}).get("count_miss", 0))

    mods_text = normalize_no_plus(mods_str)

    mods_str = score.get("mods", "")
  
    #neko API 
    payload = {
        "map_path": str(score['beatmap']['id']), 
        
        "n300": score_stats.get("count_300", score_stats.get("great", None)),
        "n100": score_stats.get("count_100", score_stats.get("ok", None)),
        "n50": score_stats.get("count_50", score_stats.get("meh", None)),
        "misses": int(misses),                   
        
        "mods": str(score.get("mods", 0)), 
        "combo": int(score['max_combo']),      
        "accuracy": float(score['accuracy']*100),    
        
        "lazer": bool(score.get('lazer', False)),          
        "clock_rate": float(score.get('speed_multiplier') or 1.0),  

        "custom_ar": float(base_ar),
        "custom_cs": float(base_cs),
        "custom_hp": float(base_hp),
        "custom_od": float(base_od),
    }

    try:
        pp_data = await localapi.get_score_pp_neko_api(payload)

        pp = pp_data.get("pp")
        max_pp = pp_data.get("no_choke_pp")
        perfect_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        perfect_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

    except Exception as e:
        print(f"neko API failed: {e}")

          
    #temp pp fix
    pp = pp if not isinstance(score.get("pp"), (int, float)) or score.get("pp") <= 0 else score.get("pp")


    accuracy = round(score['accuracy'] * 100, 2)
    accuracy_display = (
        f"{accuracy}%"
        if isinstance(score['accuracy'], (int, float))
        else "N/A"
    )    
    if score['lazer']:   
        if accuracy == 100:
            score["rank"] = 'SS'
        elif accuracy >= 90:
            if (misses == 0) and (accuracy >= 95):
                score["rank"] = 'S'
            else:
                score["rank"] = 'A'
        elif accuracy >= 80:
            score["rank"] = 'B'
        elif accuracy >= 70:
            score["rank"] = 'C'
        else:
            score["rank"] = 'D'
    
    spacer = '\n\n'
    user_link = ''
    if not image_todo_flag: 
        username = score.get("username") or score.get("user", {}).get("username")
        pp_text = f"{score.get('total_pp')}" if score.get("pp") else "0"
        global_rank_text = f"(#{score.get('global_rank'):,}" if score.get("global_rank") else "(#????"        
        rank_text = f"{username}: {pp_text}pp {global_rank_text})"
        country_flag = country_code_to_flag(country_code = score.get("country_code") or score.get("user", {}).get("country", {}).get("code"))
        user_link = f'<a href="https://osu.ppy.sh/users/{score["user"]["id"]}">{country_flag} <b>{rank_text}</b></a>\n\n'  

        beatmap_escaped = html.escape(score["beatmap_full"])
        map_text = f'<a href="{score["url"]}">{beatmap_escaped} [{stars:.2f}★]</a>\n\n'
        spacer = '\n'
    else:
        username = score.get("username") or score.get("user", {}).get("username")
        pp_text = f"{score.get('total_pp')}" if score.get("pp") else "0"
        global_rank_text = f"(#{score.get('global_rank'):,}" if score.get("global_rank") else "(#????"        
        rank_text = f"{username}: {pp_text}pp {global_rank_text})"
        country_flag = country_code_to_flag(country_code = score.get("country_code") or score.get("user", {}).get("country", {}).get("code"))
        user_link = f''  

        beatmap_escaped = html.escape(score["beatmap_full"])
        map_text = f''
        spacer = '\n'

    bpm, ar, od, cs, hp = apply_mods_to_stats(
        expected_bpm, base_ar, base_od, base_cs, base_hp,
        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
    )
    length = int(round(float(score['hit_length']) / speed_multiplier))
    
    is_cl = 'CL'
    mods_lazer = normalize_plus(mods_str)
    if str(mods_lazer) == '':
        is_cl = '+CL'   
    if score['lazer']: 
        is_cl = ""
    mods_text = f'{mods_lazer}{is_cl}'
    combo_text = f'<b>{score["max_combo"]}x</b>/{perfect_combo}x'
    map_id = score.get("beatmap", {}).get("id", 0)    
    set_id = score.get("beatmap", {}).get("beatmapset_id", 0) 
    pp_text = f'<b>{pp:.1f}</b>/{perfect_pp:.1f} <s>({max_pp:.1f}pp)</s>'
    caption = (
                 f'{user_link}{map_text}<b><i><a href="{score["url"]}">{score["rank"]}</a></i>  {mods_text}   {accuracy_display}</b>    <code>{format_osu_date(score["date"], today=is_recent)}</code>{spacer}'
                 f"{pp_text} • {combo_text} • <b>{score['count_miss']}</b>❌\n"
                 f"<code>{seconds_to_hhmmss(length)} • CS:{cs} AR:{ar} OD:{od} BPM:{bpm}</code>\n\n"
                 f'⦿ <a href="{score["url"]}">Mapset</a> by {score["mapper"]} • {score["status"].capitalize()}  <a href="http://myangelfujiya.ru/index.html?id={map_id}&set_id={set_id}">🔗</a>\n'
             )          

    img_path = None
    if image_todo_flag:
        score["sr"] = stars
        img_path = await create_beatmap_image(score)
    
    return img_path, caption
async def rs_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)   
    
    print(query.data)
    data = query.data.split("_")  # rs_prev_msgid / rs_next_msgid / disabled
    if data[1] == "disabled":
        await safe_query_answer(query)
        return

    action = data[1]
    message_id = int(data[2])

    session = user_sessions.get(message_id)
    if not session:
        await safe_query_answer(query, text="⚠️ Кнопки устарели", show_alert=False)
        return

    if str(update.effective_user.id) != session["user_id"]:
        await safe_query_answer(query, text="⛔ Не твои кнопки", show_alert=True)
        return

    new_index = session["index"]
    if action == "next" and new_index < len(session["scores"]) - 1:
        new_index += 1
    elif action == "prev" and new_index > 0:
        new_index -= 1

    score_id = str(session["scores"][new_index]["id"])
    entry = load_score_file(score_id)

    if not entry or not entry.get("ready"):
        await safe_query_answer(query)
        return

    await safe_query_answer(query)
    img_path, caption = await process_score_and_image(entry.get('raw'), image_todo_flag=rs_bg_render)

    total = len(session["scores"])
    buttons = [
        InlineKeyboardButton("⬅️", callback_data=f"rs_prev_{message_id}" if new_index > 0 else "rs_disabled"),
        InlineKeyboardButton(f"{new_index+1}/{total}", callback_data="rs_disabled"),
        InlineKeyboardButton("➡️", callback_data=f"rs_next_{message_id}" if new_index < total - 1 else "rs_disabled")
    ]
    keyboard = InlineKeyboardMarkup([buttons])

    try:
        if img_path and os.path.isfile(img_path) and os.path.getsize(img_path) > 0:
            with open(img_path, "rb") as f:
                bio = BytesIO(f.read())
            media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
            await query.edit_message_media(media=media, reply_markup=keyboard)
        else:
            link_preview = LinkPreviewOptions(
                url=entry['raw']['card2x_url'],
                is_disabled=False,
                prefer_small_media=False,
                prefer_large_media=True,
                show_above_text=True
            )
            await query.edit_message_text(
                text=caption,
                parse_mode='HTML',
                link_preview_options=link_preview,
                reply_markup=keyboard
            )

        session["index"] = new_index

        reset_remove_timer(
            context.bot,
            query.message.chat.id,
            query.message.message_id,
            RS_BUTTONS_TIMEOUT,
            cleanup=lambda: user_sessions.pop(query.message.message_id, None)
        )

    except Exception:
        traceback.print_exc()

async def create_beatmap_image(score: dict) -> str | None:
    timeout = aiohttp.ClientTimeout(total=10)
    
    def wrap_text(text, font, max_w):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_w:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
        mask = Image.new("L", img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
        img.putalpha(mask)
        return img

    def draw_text_with_shadow(draw_obj, position, text, font, fill=(255, 255, 255, 255), shadowcolor=(0, 0, 0, 255), shadow_offset=4):
        x, y = position
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                if dx == 0 and dy == 0:
                    continue
                draw_obj.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
        draw_obj.text((x, y), text, font=font, fill=fill)

    def paste_with_shadow(base_img: Image.Image, overlay_img: Image.Image, position: tuple[int, int],
                          shadow_offset: int = 5, shadow_color=(0, 0, 0, 180)):
        x, y = position
        shadow = Image.new("RGBA", overlay_img.size, shadow_color)
        shadow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        shadow_layer.paste(shadow, (x + shadow_offset, y + shadow_offset), overlay_img)
        base_img.alpha_composite(shadow_layer)
        base_img.paste(overlay_img, (x, y), overlay_img)

    cover_id = score.get("beatmapset", {}).get("id")
    if not cover_id:
        return None

    cover_path = os.path.join(COVERS_DIR, f"{cover_id}.png")

    if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
        try:
            image = Image.open(cover_path).convert("RGBA")
            print("using cached cover")
        except Exception as e:
            print(f"⚠ Ошибка открытия кэшированной обложки: {e}")
            image = Image.open(f"{BOT_DIR}/cards/assets/rs/default_cover.png").convert("RGBA")

    else:
        cover_url = (
            score["beatmapset"].get("covers", {}).get("cover@2x")
            or score["beatmapset"].get("covers", {}).get("cover")
        )
        if not cover_url:
            print("⚠ Нет ссылки на обложку, используем fallback")
            image = Image.open(f"{BOT_DIR}/cards/assets/rs/default_cover.png").convert("RGBA")

        else:
            for attempt in range(3):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(cover_url) as resp:
                            if resp.status != 200:
                                raise Exception(f"HTTP {resp.status}")
                            img_data = await resp.read()
                            image = Image.open(io.BytesIO(img_data)).convert("RGBA")
                            image.save(cover_path, format="PNG")
                            break
                except Exception as e:
                    print(f"⚠ Ошибка загрузки обложки (попытка {attempt+1}/2): {e}")
                    if attempt < 1:
                        await asyncio.sleep(1)
                    else:
                        image = Image.open("assets/default_cover.png").convert("RGBA")

    avatar_url = score["user"]["avatar_url"]
    user_id = score["user"]["id"]
    
    now = datetime.now()
    avatar_file = None
    for f in os.listdir(AVATARS_DIR):
        if f.startswith(f"{user_id}_") and f.endswith(".png"):
            path = os.path.join(AVATARS_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime < timedelta(hours=1):
                avatar_file = path
                break
            
    MAX_ATTEMPTS = 3

    if avatar_file:
        extra_img = Image.open(avatar_file).convert("RGBA")
        avatar_path = avatar_file
        print("using cached avatar")
    else:
        avatar_path = os.path.join(AVATARS_DIR, "default.png")
        extra_img = None
        for attempt_avatar in range(1, MAX_ATTEMPTS + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(avatar_url) as resp:
                        if resp.status == 200:
                            def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
                               
                                big_size = (img.size[0]*2, img.size[1]*2)
                                mask = Image.new("L", big_size, 0)
                                draw_mask = ImageDraw.Draw(mask)
                                draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                
                                mask = mask.resize(img.size, Image.LANCZOS)
                                
                                img.putalpha(mask)
                                return img
                            extra_img_data = await resp.read()
                            extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                            extra_img.thumbnail((512, 512))
                            extra_img = add_rounded_corners(extra_img, radius=12)
                            avatar_filename = f"{user_id}_{now.hour}{now.minute}.png"
                            avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
                            extra_img.save(avatar_path, format="PNG")
                            break
            except Exception as e:
                print(f"Ошибка при скачивании аватарки: {e}")

    width, height = image.size

    if width > 350:
        image = image.crop((350, 0, width - 350, height))
    else:
        pass

    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 50)
        font_info = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 40)
        font_star = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 80)
        font_username = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 60)
        font_total_pp = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 40)
    except IOError:
        font_title = ImageFont.load_default()
        font_info = ImageFont.load_default()
        font_star = ImageFont.load_default()
        font_username = ImageFont.load_default()
        font_total_pp = ImageFont.load_default()

    title = score["beatmapset"].get("title") or score["beatmapset"].get("title", "")
    artist = score["beatmapset"].get("artist", "")
    mapper = score["beatmapset"].get("creator", "unknown")
    version = score["beatmap"].get("version", "")
    sr = score["sr"]

    left_margin = 10
    right_margin = 10

    max_width = image.width - left_margin - right_margin

    title_text = f"{title} by {artist}"

    

    title_lines = wrap_text(title_text, font_title, max_width)

    y_offset = 20
    for line in title_lines:
        draw_text_with_shadow(draw, (left_margin, y_offset), line, font_title, fill=(255, 255, 255, 220), shadowcolor=(0, 0, 0, 200))
        bbox = draw.textbbox((0, 0), line, font=font_title)
        line_height = bbox[3] - bbox[1]
        y_offset += line_height + 5

    mapper_line = f"{mapper} [{version}]"
    draw_text_with_shadow(draw, (left_margin, y_offset), mapper_line, font_info, fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    star_text = f"★ {sr:.2f}"
    bbox = draw.textbbox((0, 0), star_text, font=font_star)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw_text_with_shadow(draw, (image.width - text_w - right_margin, image.height - text_h - 20), star_text, font_star, fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    
    
    extra_img = extra_img.resize((120, 120))

    if extra_img:
        extra_x = 10
        extra_y = image.height - extra_img.height - 10
        paste_with_shadow(image, extra_img, (extra_x, extra_y), shadow_offset=6, shadow_color=(0, 0, 0, 180))

        text_offset_x = extra_x + extra_img.width + 20
        text_offset_y = extra_y + 10

        text1 = score["user"]["username"]
        draw_text_with_shadow(draw, (text_offset_x, text_offset_y), text1, font_username,
                              fill=(255, 255, 255, 220), shadowcolor=(0, 0, 0, 200))

        bbox1 = draw.textbbox((0, 0), text1, font=font_username)
        line_height1 = bbox1[3] - bbox1[1]
        text2 = str(score["total_pp"]) + 'pp'
        draw_text_with_shadow(draw, (text_offset_x, text_offset_y + line_height1 + 10), text2, font_total_pp,
                              fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    score_id = f'{score["user"]["username"]}{score.get("id", "unknown")}'
    file_path = os.path.join(TEMP_DIR, f"{score_id}.png")
    image.save(file_path, format="PNG")
    print("Image saved to", file_path)
    return file_path
def get_score_path(score_id: str) -> str:
    return os.path.join(SCORES_DIR, f"{score_id}.json")
def load_score_file(score_id: str) -> dict | None:
    path = get_score_path(score_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Ошибка при загрузке файла {score_id}: {e}")
    return None
def save_score_file(score_id: str, data: dict):
    path = get_score_path(score_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ Ошибка при сохранении файла {score_id}: {e}")
async def enrich_score_lazer(session, user_id: str, score_id: str):
    cached_entry = load_score_file(score_id)
    if not cached_entry:
        return

    raw = cached_entry["raw"]
    score_page = await get_score_page(session, user_id, score_id)

    if not score_page:
        cached_entry["ready"] = True
        save_score_file(score_id, cached_entry)
        return

    lazer = True
    da_active = False
    speed_multiplier = None
    custom_values = {}
    accuracy = raw.get("accuracy")

    mods = score_page.get("mods", [])
    for mod in mods:
        if isinstance(mod, dict):
            acronym = mod.get("acronym", "").upper()
            settings = mod.get("settings", {})
        else:
            acronym = str(mod).upper()
            settings = {}

        if acronym == "DA":
            da_active = True

        if "speed_change" in settings:
            speed_multiplier = settings["speed_change"]

        for key, value in settings.items():
            if key in ["drain_rate", "circle_size", "approach_rate", "overall_difficulty"]:
                custom_values[key] = value

    accuracy = score_page.get("accuracy", accuracy)

    mods_orig = raw.get("mods", [])

    mods_clean = []
    if mods_orig:
        if isinstance(mods_orig[0], dict):
            mods_clean = [m for m in mods_orig if m.get("acronym") != "DA"]
            mods_text = "+".join(m.get("acronym", "") for m in mods_clean if "acronym" in m)
        else:
            mods_clean = [m for m in mods_orig if m != "DA"]
            mods_text = "+".join(mods_clean)
    else:
        mods_text = "NM"

    if speed_multiplier:
        mods_text += f" ({speed_multiplier}x)"
    if da_active:
        mods_text = mods_text + "+DA" if mods_text != "NM" else "+DA"

    raw.update({
        "lazer": lazer,
        "DA_values": custom_values,
        "speed_multiplier": speed_multiplier,
        "accuracy": accuracy,
        "mods": mods_text
    })

    cached_entry["raw"] = raw
    cached_entry["ready"] = True
    save_score_file(score_id, cached_entry)
async def cache_remaining_scores(user_id: str, scores: list, username: str):
    async with aiohttp.ClientSession() as session:
        for s in scores[1:]:
            score_id = str(s['id'])
            cached_entry = load_score_file(score_id)
            if not cached_entry:
                cached_entry = {"raw": s, "processed": {}, "ready": False}
                save_score_file(score_id, cached_entry)

            if not cached_entry.get("ready"):
                await enrich_score_lazer(session, str(s['user']['id']), score_id)
                cached_entry = load_score_file(score_id)
                cached_entry["ready"] = True
                save_score_file(score_id, cached_entry)
            await asyncio.sleep(LXML_TIMEOUT)

#not-important-cmd TODO remove?
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
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_HELP_COMMAND} секунд"
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
            full_text = help_text + help_hint        
            entities = [
                MessageEntity(
                    type="expandable_blockquote",
                    offset=0,                     
                    length=len(help_text)+12         
                )
            ]        
            max_attempts = 3
            for _ in range(max_attempts):
                await update.message.reply_text(full_text, entities=entities)
                return
        
    except Exception as e:
        print(f"Ошибка при doubt: {e}")
async def doubt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        await update.message.delete()

        can_run = await check_user_cooldown(
            command_name="doubt",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_GIFS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_GIFS_COMMANDS} секунд"
        )
        if not can_run:
            return
        
        message_thread_id = update.message.message_thread_id

        with open(GIF_DOUBT_PATH, "rb") as animation_file:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=animation_file,
                message_thread_id=message_thread_id
            )

    except Exception as e:
        print(f"Ошибка при doubt: {e}")
async def blacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        await update.message.delete()

        can_run = await check_user_cooldown(
            command_name="blacks",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_GIFS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_GIFS_COMMANDS} секунд"
        )
        if not can_run:
            return
        
        message_thread_id = update.message.message_thread_id

        with open(GIF_BLACKS_PATH, "rb") as animation_file:
            await context.bot.send_sticker(
                chat_id=update.effective_chat.id,
                sticker=animation_file,
                message_thread_id=message_thread_id
            )

    except Exception as e:
        print(f"Ошибка при blacks: {e}")
async def random_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="random_image",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_PICS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_PICS_COMMANDS} секунд"
        )
        if not can_run:
            return

        if update.effective_chat.type != "supergroup":
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
                    asyncio.create_task(delete_response([user_msg, bot_msg], delay=30))

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
async def delete_response(resp, delay: int = 10):
    await asyncio.sleep(delay)
    if isinstance(resp, list):
        for r in resp:
            try:
                await r.delete()
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")
    else:
        try:
            await resp.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

#challenge cmd TODO v2
       
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        topic_id = getattr(update.effective_message, "message_thread_id", None)        
        points_data = temp.load_json(POINTS_FILE, {})
        if not points_data:
            await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text="🏆 Лидерборд пуст", parse_mode="HTML")
            return
        
        sorted_lb = sorted(points_data.items(), key=lambda x: x[1], reverse=True)
        text = "🏆 <b>Лидерборд челленджей:</b>\n"
        for i, (uid, pts) in enumerate(sorted_lb[:10], start=1):
            saved_name = await auth.check_osu_verified(str(uid))
            display_name = saved_name if saved_name else uid 
            text += f"{i}. {display_name} — <b><u>{pts}</u></b>pt\n"

        text += f"\n\n👑 <b>Сезонный:</b>\n n/a"

        await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text=text, parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text=f"ошибка {e}", parse_mode="HTML")

async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)
    
    try:
        topic_id = getattr(update.effective_message, "message_thread_id", None) 
        text = "нет челленджа сегодня 😞"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, message_thread_id=topic_id, parse_mode="HTML")
        
    except Exception as e:
        print(e)

async def get_random_beatmap_from_random_pack(max_attempts=5):
    async with aiohttp.ClientSession() as session:
        token = await get_osu_token()
        packs_url = "https://osu.ppy.sh/api/v2/beatmaps/packs?type=standard"
        headers = {"Authorization": f"Bearer {token}"}
        print('🔻 API request (get_random_beatmap_from_random_pack 1/2)')
        async with session.get(packs_url, headers=headers) as resp:
            data = await resp.json()

        packs = data.get("beatmap_packs", [])
        # ruleset_id == 0
        packs = [p for p in packs if p.get("ruleset_id") == None]

        if not packs:
            return None

        for _ in range(max_attempts):
            pack = random.choice(packs)
            pack_tag = pack["tag"]

            pack_detail_url = f"https://osu.ppy.sh/api/v2/beatmaps/packs/{pack_tag}"
            print('🔻 API request (get_random_beatmap_from_random_pack 2/2)')
            async with session.get(pack_detail_url, headers=headers) as resp:
                pack_detail = await resp.json()

            # ruleset_id == 0
            beatmapsets =  pack_detail.get("beatmapsets", [])

            if beatmapsets:
                beatmapset = random.choice(beatmapsets)
                return {
                    "pack_tag": pack_tag,
                    "pack_name": pack["name"],
                    "beatmapset_id": beatmapset["id"],
                    "artist": beatmapset["artist"],
                    "title": beatmapset["title"],
                    "creator": beatmapset["creator"],
                    "url": f"https://osu.ppy.sh/beatmapsets/{beatmapset['id']}"
                }

        return None

#mods&mappers cmd TODO add single api req
async def start_mappers(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mappers(update, context, user_request))
async def mappers(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="mappers",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    MAX_ATTEMPTS = 3

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/mappers fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            
            if isinstance(best_pp, list) and best_pp:
                

                mapper_counter = defaultdict(lambda: {"pp_sum": 0.0, "count": 0})

                for score in best_pp:
                    mapper = score.get("mapper", "Unknown")
                    raw_pp = score.get("pp", 0.0) or 0.0

                    if "weight_percent" in score:
                        weighted_pp = raw_pp * (score["weight_percent"] / 100.0)
                    else:
                        weighted_pp = raw_pp

                    mapper_counter[mapper]["pp_sum"] += weighted_pp
                    mapper_counter[mapper]["count"] += 1

                sorted_mappers = sorted(
                    mapper_counter.items(),
                    key=lambda x: (x[1]["count"], x[1]["pp_sum"]),
                    reverse=True
                )

                top_mappers = sorted_mappers[:10]

                mapper_width = max(len(mapper) for mapper, _ in top_mappers) if top_mappers else 0
                pp_width = max(len(f"{data['pp_sum']:.2f}") for _, data in top_mappers) if top_mappers else 0
                count_width = max(len(str(data['count'])) for _, data in top_mappers) if top_mappers else 0

                table_lines = [
                    f"{'Mapper':<{mapper_width}} | {'PP':>{pp_width}} | {'#':>{count_width}}",
                    f"{'-'*mapper_width}-+-{'-'*pp_width}-+-{'-'*count_width}"
                ]
                for mapper, data in top_mappers:
                    table_lines.append(
                        f"{mapper:<{mapper_width}} | {data['pp_sum']:>{pp_width}.2f} | {data['count']:>{count_width}}"
                    )

                table_text = "\n".join(table_lines)

                username = user_data["username"]
                stats = user_data["statistics"]
                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )
                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

                text = f"{user_link}\n\n<pre>{table_text}</pre>"
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"
                    )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных или ошибка сети")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при mappers (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
async def start_mods(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mods(update, context, user_request))               
async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="mods",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/mods fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = "N/A"
                print(e)


            if isinstance(best_pp, list) and best_pp:
                mod_counter = Counter()
                combo_counter = Counter()
                # combo_pp_sum = defaultdict(float)
                combo_pp_weighted_sum = defaultdict(float)

                for score in best_pp:
                    mods = score.get("mods", [])
                    combo = format_mods(mods)

                    if mods:
                        for m in mods:
                            mod_counter[m] += 1
                    else:
                        mod_counter["NM"] += 1

                    combo_counter[combo] += 1

                    pp_value = score.get("pp", 0.0) or 0.0
                    weight_percent = score.get("weight_percent", 0.0) or 0.0

                    # combo_pp_sum[combo] += pp_value
                    combo_pp_weighted_sum[combo] += pp_value * (weight_percent / 100)

                total_scores = len(best_pp)

                fav_mods_str = format_blocks_percent(mod_counter, total_scores, per_row=4)
                fav_combos_str = format_blocks_percent(combo_counter, total_scores, per_row=3)
                # profit_combos_str = format_blocks_pp(combo_pp_sum, per_row=3)
                weighted_combos_str = format_blocks_pp(combo_pp_weighted_sum, per_row=3)

                username = user_data["username"]                
                stats = user_data["statistics"]

                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )

                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'                
               
                text = (
                    f"{user_link}\n\n"
                    "⦿ <b><u>Top100 mods:</u></b>\n\n"
                    f"<b>Favourite mods</b>\n{fav_mods_str}\n\n"
                    f"<b>Favourite mod combinations</b>\n{fav_combos_str}\n\n"
                    # f"<b>Profitable mod combinations (pp)</b>\n{profit_combos_str}\n\n"
                    f"<b>Profitable mod combinations (pp)</b>\n{weighted_combos_str}"
                )

                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"            
                )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при mods (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
#profile&card cmd TODO card rework
async def start_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, user_request))
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="profile",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    MAX_ATTEMPTS = 3

    user_id = str(update.effective_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/p Fujiya` <- никнейм"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    elif update.callback_query:
        query = update.callback_query
        if query.message.text or query.message.caption:
            temp_message = await query.message.edit_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )
        else:
            temp_message = await query.message.reply_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )

    message_authors[temp_message.message_id] = update.effective_user.id

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            if isinstance(best_pp, list) and best_pp:                
                username = user_data["username"]
                stats = user_data["statistics"]
                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )
                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                hours = user_data['statistics']['play_time'] // 3600
                plays = stats.get('play_count') if stats.get('play_count') else "0"                
                accuracy = stats.get('hit_accuracy') if stats.get('hit_accuracy') else "0"
                medals = len(user_data['user_achievements'])
                
                level_data = stats.get('level', {})
                current = level_data.get('current', 0)
                progress = level_data.get('progress', 0)

                level = float(f"{current}.{progress}")

                try:
                    team = user_data['team']['short_name']
                    team_url = f"https://osu.ppy.sh/teams/{user_data['team']['id']}"
                    team_link = f'<a href="{team_url}">{team}</a>'
                except:
                    team_link = '✖️' 
                                
                peak_rank = user_data['rank_highest']['rank']

                def format_osu_date(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S", flag = True) -> str:
                    try:
                        if date_str.endswith("Z"):
                            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        else:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception as e:
                        print(f"Ошибка: {e}")
                        return "N/A"

                    formatted = dt.strftime(fmt)

                    now = datetime.now(timezone.utc)
                    delta = now - dt

                    if delta.days >= 365:
                        years = delta.days // 365
                        ago = f"{years} years ago"
                    elif delta.days >= 30:
                        months = delta.days // 30
                        ago = f"{months} months ago"
                    elif delta.days > 0:
                        ago = f"{delta.days} days ago"
                    else:
                        hours = delta.seconds // 3600
                        ago = f"{hours} hours ago" if hours > 0 else "less than an hour ago"

                    if flag:
                        return f"{formatted} ({ago})"
                    else:
                        return f"({formatted})"
                
                peak_date = format_osu_date(user_data['rank_highest']['updated_at'], "%d.%m.%Y", flag=False)
                joined = format_osu_date(user_data['join_date'], "%Y-%m-%d %H:%M:%S")

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'                 

                text =(
                    f"{user_link}\n\n"
                    f"Accuracy: <code> {accuracy:.2f}%</code>  •  Level:<code> {level}</code>\n"
                    f"Playcount: <code> {plays:,}</code>   (<code>{hours} hrs</code>)\n"
                    f"Medals: <code> {medals} </code> •  Team: {team_link}\n"
                    f"Peak rank: <code> #{peak_rank:,}</code>   {peak_date}\n\n"
                    f"⦿ Joined {joined}\n\n"
                ) 

                if query:
                    for msg_id, author_id in list(message_authors.items()):
                        if author_id == query.from_user.id:
                            try:
                                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=msg_id)
                            except:
                                pass
                            message_authors.pop(msg_id, None)

                    new_msg = await safe_edit_message(
                        temp_message,
                        text,
                        parse_mode="HTML",
                        # reply_markup=get_profile_keyboard("profile")
                    )
                    message_authors[new_msg.message_id] = query.from_user.id
                    return
                else:
                    try:
                        new_msg = await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=temp_message.message_id,
                            text=text,
                            parse_mode="HTML", 
                            # reply_markup=get_profile_keyboard("profile")
                        )
                        message_authors[new_msg.message_id] = update.effective_user.id
                        return
                    except:
                        new_msg = await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            parse_mode="HTML", 
                            # reply_markup=get_profile_keyboard("profile")
                        )
                        message_authors[new_msg.message_id] = update.effective_user.id

            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных или ошибка сети")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при profile (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
async def create_profile_image(user_data: dict, best_pp: str) -> str | None:
    final_w, final_h = 1000, 400

    cover_url = user_data.get("cover_url")
    if cover_url:
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(cover_url, timeout=timeout) as resp:
                    if resp.status == 200:
                        bg_bytes = await resp.read()
                        banner = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
                        bw, bh = banner.size
                        target_ratio = final_w / final_h
                        banner_ratio = bw / bh
                        if banner_ratio > target_ratio:
                            new_w = int(bh * target_ratio)
                            left = (bw - new_w) // 2
                            banner = banner.crop((left, 0, left + new_w, bh))
                        else:
                            new_h = int(bw / target_ratio)
                            top = (bh - new_h) // 2
                            banner = banner.crop((0, top, bw, top + new_h))
                        banner = banner.resize((final_w, final_h), Image.LANCZOS)
                    else:
                        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                print(f"Failed to load cover_url: {e}")
                banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
    else:
        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))

    draw = ImageDraw.Draw(banner)

    try:
        font_name = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 60)
        font_stats = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 28)
        font_small = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 24)
    except IOError:
        font_name = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def draw_text_with_shadow_3(draw, pos, text, font, fill, shadowcolor):
        x, y = pos
        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw_obj, position, text, font, fill=(255, 255, 255, 255),
                              shadowcolor=(0, 0, 0, 255), shadow_offset=3):
        x, y = position
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                if dx == 0 and dy == 0:
                    continue
                draw_obj.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
        draw_obj.text((x, y), text, font=font, fill=fill)

    avatar_top = 35
    async with aiohttp.ClientSession() as session:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(user_data["avatar_url"], timeout=timeout) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_img = avatar_img.resize((200, 200))
                    mask = Image.new("L", avatar_img.size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    corner_radius = 20
                    mask_draw.rounded_rectangle((0, 0, 200, 200), radius=corner_radius, fill=255)
                    avatar_img.putalpha(mask)
                    shadow = Image.new("RGBA", avatar_img.size, (0, 0, 0, 180))
                    banner.paste(shadow, (50 + 5, avatar_top + 5), mask)
                    banner.paste(avatar_img, (50, avatar_top), avatar_img)                  
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"Failed to load avatar_url: {e}")           

    try:
        short_name = ""
        team_flag_url = user_data.get("team", {}).get("flag_url")
        if team_flag_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(team_flag_url) as resp:
                    if resp.status == 200:
                        flag_bytes = await resp.read()
                        flag_img = Image.open(io.BytesIO(flag_bytes)).convert("RGBA")
                        fw, fh = flag_img.size
                        scale_factor = 200 / fw
                        new_w = int(fw * scale_factor)
                        new_h = int(fh * scale_factor)
                        flag_img = flag_img.resize((new_w, new_h), Image.LANCZOS)
                        
                        shadow = Image.new("RGBA", flag_img.size, (0, 0, 0, 180))
                        
                        flag_alpha = flag_img.split()[3]

                        flag_y = avatar_top + 200 + 10
                        shadow_offset = (5, 5) 

                        banner.paste(shadow, (50 + shadow_offset[0], flag_y + shadow_offset[1]), flag_alpha)
                        
                        banner.paste(flag_img, (50, flag_y), flag_img)

        short_name = "team tag:  " + user_data.get("team", {}).get("short_name", "")
        if short_name:
            flag_y_bottom = avatar_top + 200 + 15 + (new_h if team_flag_url else 0)
            draw_text_with_shadow_3(draw, (50, flag_y_bottom + 5), short_name, font_stats, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))
    except Exception as e: 
        print(e)
        
    username = user_data["username"]
    draw_text_with_shadow(draw, (280, 40), username, font_name)

    stats = user_data["statistics"]
    country_rank = stats.get("rank", {}).get("country", None)

    def hue_to_rgba(hue, saturation=1.0, lightness=0.5, alpha=255):
        if hue is None:
            hue = 349
        h = (hue % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)
        return (int(r * 255), int(g * 255), int(b * 255), alpha)

    def draw_text_with_shadow_2(draw, pos, text, font, fill, shadowcolor):
        x, y = pos
        
        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)
       
        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw, pos, text, font, fill, shadowcolor):
        x, y = pos
        
        draw.text((x + 1, y + 1), text, font=font, fill=shadowcolor)
        
        draw.text((x, y), text, font=font, fill=fill)

    def draw_stat_line(draw, pos, key_text, value_text, font_key, font_value,
                    key_fill, key_shadow, value_fill, value_shadow, gap=8):
        x, y = pos
        
        draw_text_with_shadow(draw, (x, y), key_text, font_key, fill=key_fill, shadowcolor=key_shadow)
        
        bbox = draw.textbbox((x, y), key_text, font=font_key)
        key_w = bbox[2] - bbox[0]
        
        draw_text_with_shadow(draw, (x + key_w + gap, y), value_text, font_value, fill=value_fill, shadowcolor=value_shadow)

    stat_lines = [
        f"PP: {round(stats.get('pp', 0), 2)}",
        f"Country Rank: #{country_rank}" if country_rank else "Country Rank: N/A",
        f"Accuracy: {round(stats.get('hit_accuracy', 0), 2)}%",
        f"Playcount: {stats.get('play_count', 0):,}",
        f"Max Combo: {stats.get('maximum_combo', 0):,}",
        f"Playtime: {stats.get('play_time', 0) // 3600}h",
        f"Hits/Play: {round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)}",
        f" ",
        f" ",
        f"Max PP: {best_pp}",       
        f"Replays Watched: {stats.get('replays_watched_by_others', 0):,}",         
    ]

    profile_hue = user_data.get("profile_hue", 211)
    glow_color = hue_to_rgba(profile_hue, saturation=1, lightness=0.5, alpha=180)

    overlay_x, overlay_y = 270, 106
    overlay_w, overlay_h = 680, 240
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, 190))
    banner.paste(overlay, (overlay_x, overlay_y), overlay)

    col_gap = 340
    left_x, right_x = 280, 280 + col_gap
    y_start = 120

    for i, line in enumerate(stat_lines):
        col = i % 2
        row = i // 2
        x_pos = left_x if col == 0 else right_x
        y_pos = y_start + row * 32

        if ": " in line:
            key_text, value_text = line.split(": ", 1)
            key_text += ":"
        else:
            key_text, value_text = line, ""

        draw_stat_line(
            draw, (x_pos, y_pos),
            key_text, value_text,
            font_stats, font_stats,
            key_fill=(255, 255, 255, 220), key_shadow=(0, 0, 0, 180),
            value_fill=glow_color, value_shadow=(0, 255, 255, 180),
            gap=8
        )

    lvl_current = stats.get("level", {}).get("current", 0)
    lvl_progress = stats.get("level", {}).get("progress", 0)
    bar_x, bar_y = 280, final_h - 35
    bar_width, bar_height = 480, 15
    
    shadow_offset = (10, 10) 
    shadow_color = (0, 0, 0, 200) 
    shadow_radius = 35

    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_draw.rounded_rectangle(
        [bar_x + shadow_offset[0], bar_y + shadow_offset[1], bar_x + bar_width + shadow_offset[0], bar_y + bar_height + shadow_offset[1]],
        radius=12,
        fill=shadow_color
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_radius))

    banner = Image.alpha_composite(banner, shadow_layer)

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                        radius=12, fill=(60, 60, 60, 200))
    fill_width = int(bar_width * (lvl_progress / 100))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                        radius=12, fill=(glow_color))
    
    text = f"Level {lvl_current} ({lvl_progress}%)"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = bar_x + bar_width + 10
    text_y = bar_y + (bar_height - text_h) // 2

    draw_text_with_shadow_2(draw, (text_x, text_y), text, font_small, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))

    def draw_neon_glow(base_img, points, glow_color, glow_width=15, blur_radius=10):       
        glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        glow_draw.line(points, fill=glow_color, width=glow_width, joint="curve")

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))

        base_img.alpha_composite(glow_layer)

    def draw_gradient_line(draw, points, start_color, end_color, width=3):       
        n = len(points)
        for i in range(n - 1):           
            t = i / (n - 2) if n > 2 else 0
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            a = int(start_color[3] + (end_color[3] - start_color[3]) * t)

            color = (r, g, b, a)
            draw.line([points[i], points[i+1]], fill=color, width=width, joint="curve")

    extra_height = 200
    new_banner = Image.new("RGBA", (banner.width, banner.height + extra_height), (30, 30, 30, 255))
    new_banner.paste(banner, (0, 0))
    banner = new_banner
    draw = ImageDraw.Draw(banner)

    background_img = Image.open(GRAPH_PNG).convert("RGBA")

    banner.paste(background_img, (0, 400), background_img)

    rank_history = user_data.get("rank_history", {}).get("data")
    if rank_history:
        graph_x = 50
        graph_y = banner.height - extra_height + 20
        graph_width = banner.width - 100
        graph_height = extra_height - 40

        min_rank = min(rank_history)
        max_rank = max(rank_history)
        rank_range = max_rank - min_rank if max_rank != min_rank else 1

        points = []
        for i, rank in enumerate(rank_history):
            x = graph_x + (i / (len(rank_history) - 1)) * graph_width
            y = graph_y + ((rank - min_rank) / rank_range) * graph_height

            points.append((x, y))

        draw_neon_glow(banner, points, glow_color, glow_width=15, blur_radius=15)

        start_color = (255, 255, 255, 255)
        end_color = glow_color
        draw_gradient_line(draw, points, start_color, end_color, width=3)

        draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], outline=(150, 150, 150, 255), width=1)

    points = []
    for i, rank in enumerate(rank_history):
        x = graph_x + (i / (len(rank_history) - 1)) * graph_width
        y = graph_y + graph_height - ((rank - min_rank) / rank_range) * graph_height
        points.append((x, y))

    rank_text = f"#{stats.get('global_rank'):,}" if stats.get("global_rank") else "Global Rank: N/A"
    bbox = draw.textbbox((0, 0), rank_text, font=font_name)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    last_point_x, last_point_y = points[-1]
    mid_y = graph_y + graph_height / 2
    padding = 5

    text_x = graph_x + graph_width - text_w

    if last_point_y > mid_y:      
        text_y = max(last_point_y - text_h - padding, graph_y)
    else:        
        text_y = min(last_point_y + padding, graph_y + graph_height - text_h)

    draw_text_with_shadow(
        draw,
        (text_x, text_y),
        rank_text,
        font=font_name,
        fill=(255, 255, 255, 200),
        shadowcolor=(0, 0, 0, 180)
    )

    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    banner.save(tmp_file.name, "PNG")
    tmp_file.close()
    return tmp_file.name
async def start_card(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(card(update, context, user_request))
async def card(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="card",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.effective_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )
    elif query:
        if query.message.text or query.message.caption:
            temp_message = await query.message.edit_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )
        else:
            temp_message = await query.message.reply_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/c Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    message_authors[temp_message.message_id] = update.effective_user.id
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            
            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(user_id), {}) 
            new_card = user_settings.get("new_card", True)   

            if not new_card:
                try:
                    best_pp = await asyncio.wait_for(get_best_pp_by_username(username, token=token), timeout=10)
                except Exception as e:
                    best_pp = "N/A"
                    print(e)

                img_path = await asyncio.wait_for(create_profile_image(user_data, best_pp), timeout=15)
                if not img_path:
                    print('err in card "not img_path"')
                    return
                
                with open(img_path, "rb") as f:
                    try:
                        await message.reply_photo(
                            InputFile(f),
                        )
                    except:
                        await message.reply_photo(
                            InputFile(f),
                            )
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                except:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)

                os.remove(img_path)
                return         

            else:            
        
                try:
                    user_id = user_data["id"]  # изменить на percent("NM") < 10: другом количестве скоров!!!
                    best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id, limit=30, plain=True), timeout=10)
                except Exception as e:
                    best_scores = "N/A"
                    print(e)  

                scores = []
                unique_maps = set()
                
                maps_ids = []
                for score in best_scores:
                    map_id = score["beatmap"]["id"]
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (card):", failed)

                for score in best_scores:
                    map_id = score["beatmap"]["id"]
                    path = results.get(map_id, None)
                    unique_maps.add((map_id, tuple(score.get("mods", []))))
                    stats = score["statistics"]
                    count_300 = stats.get("count_300", 0)
                    count_100 = stats.get("count_100", 0)
                    count_50 = stats.get("count_50", 0)
                    count_miss = stats.get("count_miss", 0)    
                    if is_legacy_score(score): lazer = False 
                    else: lazer = True    
                    
                    score["lazer"] = lazer       
                    scores.append(Score(
                        map_id=map_id,
                        count_300=count_300,
                        count_100=count_100,
                        count_50=count_50,
                        count_miss=count_miss,
                        path=path,
                        mods=score.get("mods", []), 
                        acc=score.get("accuracy", 1.0),            
                        max_combo=score.get("max_combo", 0),
                        lazer=lazer
                    ))

                #neko api 
                scores_payload = []
                for score in best_scores:
                    stats = score["statistics"]
                    scores_payload.append({
                        "map_id": score["beatmap"]["id"],
                        "n320": stats.get("count_geki", 0),
                        "n300": stats.get("count_300", 0),
                        "n200": stats.get("count_katu", 0),
                        "n100": stats.get("count_100", 0),
                        "n50":  stats.get("count_50", 0),
                        "misses": stats.get("count_miss", 0),
                        "combo": score.get("max_combo"),
                        "mods": str(score.get("mods", "")),
                        "accuracy": float(score["accuracy"] * 100.0),
                        "set_on_lazer": bool(score.get("lazer", True)),
                        "large_tick_hit": stats.get("count_large_tick_hit", 0),
                        "small_tick_hit": stats.get("count_small_tick_hit", 0),
                        "small_tick_miss": stats.get("count_small_tick_miss", 0),
                        "slider_tail_hit": stats.get("count_slider_tail_hit", 0),
                    })

                payload = {
                    "mode": "Osu",
                    "scores": scores_payload
                }

                try:
                    skills = await localapi.get_pp_parts_neko_api(payload)

                except Exception as e:
                    print(f"error calling Rust API: {e}")

                acc, aim, speed = skills["acc"], skills["aim"], skills["speed"]
                acc_total = skills["acc_total"]
                aim_total = skills["aim_total"]
                speed_total = skills["speed_total"]
               

                if os.path.exists(USERS_SKILLS_FILE):
                    with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
                        users_skills = json.load(f)
                else:
                    users_skills = {}


                total = acc + aim + speed 

                users_skills[username] = {
                    "kind": skills.get("kind", "Osu"),
                    "values": {k: round(v, 2) for k, v in skills.items()},
                    "total": round(acc_total + aim_total + speed_total, 2)
                }

                with open(USERS_SKILLS_FILE, "w", encoding="utf-8") as f:
                    json.dump(users_skills, f, indent=4, ensure_ascii=False)

                print(f"skills of {username} saved to {USERS_SKILLS_FILE}")

                bg, title = (get_title(aim, speed, acc, scores)) 

                username = user_data["username"]
                stats = user_data["statistics"]
                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank = f"{stats.get('global_rank'):,}" if stats.get("global_rank") else "N/A"
                country_rank = f"{stats.get('country_rank'):,}" if stats.get("country_rank") else "N/A"            
                country_code = user_data["country_code"]
    
                medals = len(user_data['user_achievements'])
                
                level_data = stats.get('level', {})
                current = level_data.get('current', 0)
                progress = level_data.get('progress', 0)

                level = float(f"{current}.{progress}")

                avatar_url = user_data["avatar_url"]
                user_id = user_data["id"]
                
                now = datetime.now()
                avatar_file = None
                for f in os.listdir(AVATARS_DIR):
                    if f.startswith(f"{user_id}_") and f.endswith(".png"):
                        path = os.path.join(AVATARS_DIR, f)
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        if now - mtime < timedelta(hours=1):
                            avatar_file = path
                            break
                
                if avatar_file:
                    extra_img = Image.open(avatar_file).convert("RGBA")
                    avatar_path = avatar_file
                    print("using cached avatar")
                else:
                    avatar_path = os.path.join(AVATARS_DIR, "default.png")
                    extra_img = None
                    for attempt_avatar in range(1, MAX_ATTEMPTS + 1):
                        try:
                            timeout = aiohttp.ClientTimeout(total=3)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.get(avatar_url) as resp:
                                    if resp.status == 200:
                                        def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:                                            
                                            big_size = (img.size[0]*2, img.size[1]*2)
                                            mask = Image.new("L", big_size, 0)
                                            draw_mask = ImageDraw.Draw(mask)
                                            draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                            
                                            mask = mask.resize(img.size, Image.LANCZOS)
                                            
                                            img.putalpha(mask)
                                            return img
                                        extra_img_data = await resp.read()
                                        extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                                        extra_img.thumbnail((512, 512))
                                        extra_img = add_rounded_corners(extra_img, radius=12)
                                        avatar_filename = f"{user_id}_{now.hour}{now.minute}.png"
                                        avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
                                        extra_img.save(avatar_path, format="PNG")
                                        break
                        except Exception as e:
                            print(f"Ошибка при скачивании аватарки: {e}")

                # width, height = image.size

                # if width > 350:
                #     image = image.crop((350, 0, width - 350, height))
                # else:
                #     pass

                # avatar_path = os.path.join(AVATARS_DIR, "default.png")

                img_path = make_card(
                    title=title,
                    bg=bg,
                    username=username,
                    country_code=country_code, 
                    avatar_path=avatar_path,
                    accuracy=acc,
                    aim=aim,
                    speed=speed,
                    global_rank=global_rank,
                    country_rank=country_rank,
                    level=level,
                    medals=medals,
                    mode="Standard",########################################
                    output=f"{CARDS_DIR}/{user_data['id']}.png",
                    aim_total=aim_total,
                    speed_total=speed_total,
                    acc_total=acc_total,
                )

                        
                with open(img_path, "rb") as f:
                        try:
                            await message.reply_photo(
                                InputFile(f),
                            )
                        except:
                            await message.reply_photo(
                                InputFile(f),
                            )
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                except:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)

                os.remove(img_path)
                return

        except Exception as e:
            print(f"Ошибка при card (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
def is_legacy_score(score: dict) -> bool:
    score_id = score.get("score_id")
    legacy_score_id = score.get("legacy_score_id")
    score_val = score.get("score")

    if not score_id or score_id == 0:
        if legacy_score_id or score_val:
            return True
    return False
async def beatmap_txt_downlaod(session: aiohttp.ClientSession, map_id: int) -> str | None:
    path_to_map = os.path.join(BEATMAPS_DIR, f"{map_id}.osu")

    if os.path.exists(path_to_map):
        file_age = time.time() - os.path.getmtime(path_to_map)
        if file_age < CACHE_TTL:
            print('🍡 using cache (beatmap_txt_downlaod)')
            return path_to_map
        else:
            os.remove(path_to_map)

    url = f"https://osu.ppy.sh/osu/{map_id}"
    try:
        print('🔻 beatmap request (beatmap_txt_downlaod)')
        async with session.get(url, timeout=3) as resp:
            if resp.status != 200:
                return None
            text = await resp.text()
    except Exception as e:
        print(f"Ошибка при скачивании карты {map_id}: {e}")
        return None

    with open(path_to_map, "w", encoding="utf-8") as f:
        f.write(text)

    return path_to_map

async def fetch_txt_beatmaps(map_ids, retries: int = 3, batch_size: int = 5, delay: float = 0.05):
    results = {}
    failed = map_ids[:]

    async with aiohttp.ClientSession() as session:
        for attempt in range(1, retries + 1):
            if not failed:
                break

            new_failed = []
            for i in range(0, len(failed), batch_size):
                batch = failed[i:i + batch_size]

                tasks = [beatmap_txt_downlaod(session, mid) for mid in batch]
                done = await asyncio.gather(*tasks, return_exceptions=True)

                for mid, result in zip(batch, done):
                    if isinstance(result, Exception) or result is None:
                        new_failed.append(mid)
                    else:
                        results[mid] = result

                await asyncio.sleep(delay)

            failed = new_failed

    return results, failed

class Score:
    def __init__(self, map_id, count_300, count_100, count_50, count_miss, path, mods, acc, max_combo, lazer):
        self.map_id = map_id
        self.count_300 = count_300
        self.count_100 = count_100
        self.count_50 = count_50
        self.count_miss = count_miss
        self.path = path
        self.mods = mods
        self.acc = acc
        self.max_combo = max_combo
        self.lazer = lazer

def get_prefix(value: float) -> str:
    if value < 10: return "Newbie"
    if value < 20: return "Novice"
    if value < 30: return "Rookie"
    if value < 40: return "Apprentice"
    if value < 50: return "Advanced"
    if value < 60: return "Outstanding"
    if value < 70: return "Seasoned"
    if value < 80: return "Professional"
    if value < 85: return "Expert"
    if value < 90: return "Master"
    if value < 95: return "Legendary"
    return "God"


def get_suffix(aim: float, speed: float, acc: float, tol: float = 3.0) -> str:   
    if abs(aim - speed) < tol and abs(speed - acc) < tol:
        return "All-Rounder"
    if acc > aim and acc > speed and abs(aim - speed) < tol:
        return "Rhythm Enjoyer"
    if aim > acc and aim > speed and abs(acc - speed) < tol:
        return "Whack-A-Mole"
    if speed > aim and speed > acc and abs(aim - acc) < tol:
        return "Masher"
    if acc > speed and aim > speed:
        return "Sniper"
    if acc > aim and speed > aim:
        return "Ninja"
    if aim > acc and speed > acc:
        return "Gunslinger"
    return "Undefined"


def get_title(aim: float, speed: float, acc: float, scores) -> str:
    max_skill = max(aim, speed, acc)
    prefix = get_prefix(max_skill)

    description = get_description(scores, mode="osu")

    suffix = get_suffix(aim, speed, acc, 10) # для 100 скоров = 3

    return prefix, f"{prefix} {description} {suffix}"


def get_description(scores: dict, mode) -> str:
    mods_counter = Counter()
    total = len(scores) or 1

    for score in scores:
        mods = score.mods or ["NM"]
        for m in mods:
            mods_counter[m] += 1

    def percent(mod: str) -> float:
        return mods_counter[mod] * 100 / total

    if percent("NM") > 70:
        return "Mod-Hating"
    
    bonus_title = ""
    if mode == "osu":
        if percent("HD") > 60:
            bonus_title = "HD-Abusing"
        if percent("HR") > 60:
            bonus_title = "Ant-Clicking"
        if percent("EZ") > 15:
            bonus_title = "Patient"
    
    # if percent("HD") > 60:
    #     return random.choice(["HD-Abusing", "Ghost-Fruits", "Brain-Lag"])
    # if percent("HR") > 60:
    #     return random.choice(["Ant-Clicking", "Zooming", "Pea-Catching"])
    # if percent("EZ") > 15:
    #     return random.choice(["Patient", "Training-Wheels", "3-Life"])
        
    if percent("DT") + percent("NC") > 60:
        return f"Speedy {bonus_title}"
    if percent("HT") > 30:
        return f"Slow-Mo {bonus_title}"
    if percent("FL") > 15:
        return f"Blindsighted {bonus_title}"
    if percent("SO") > 20:
        return f"Lazy-Spin {bonus_title}"
    if percent("MR") > 30:
        return f"Unmindblockable {bonus_title}"

    if percent("NM") < 6: # изменить при другом количестве скоров!!!
        return "Mod-Loving"

    return "Versatile"



def make_card(title, bg, username, country_code, avatar_path, accuracy, aim, speed,
              global_rank, country_rank, level, medals, mode, output="card.png", acc_total=None, aim_total=None, speed_total=None):

    bg_name = "novice" 
    if bg is not None:
        bg_name = bg  

    card = Image.open(f"{BOT_DIR}/cards/assets/backgrounds/{bg_name}.png").convert("RGBA")
    draw = ImageDraw.Draw(card)

    asset = Image.open(f"{BOT_DIR}/cards/assets/branding/outline.png").convert("RGBA")
    card.paste(asset, (0, 0), mask=asset.split()[3])

    asset = Image.open(f"{BOT_DIR}/cards/assets/gamemodes/{mode}.png").convert("RGBA")
    card.paste(asset, (808, 53), asset)

    asset = Image.open(f"{BOT_DIR}/cards/assets/branding/icon.png").convert("RGBA")
    card.paste(asset, (0, 1260-184), asset)
   
    font_black_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 70)
    font_black_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 48)
    font_bold_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 68)
    font_bold_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 50)
    font_bold_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 42)
    font_bold_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 35)
    font_bold_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 26)       
    font_bold_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-BoldItalic.ttf", 50)
    font_bold_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-BoldItalic.ttf", 34)
    font_light_italic_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 48)
    font_light_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 42)
    font_light_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 32)
    font_light_italic_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 34)
    font_medium_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-MediumItalic.ttf", 32)
    font_regular_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 68)
    font_regular_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 26)
    font_thin_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Thin.ttf", 48)
    font_bold_nano_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 26)     

    # # Верхний заголовок
    # draw.text((52, 35),title,font=font_bold_italic_med, fill=(200, 200, 200))

    flag_path = f"{BOT_DIR}/cards/assets/flags/{country_code}.png"    
    flag_img = Image.open(flag_path).convert("RGBA")


    block_left = 52
    block_right = 980 - 250
    max_width = block_right - block_left

    words = title.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        line_width = draw.textlength(test_line, font=font_bold_italic_med)
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    lines = lines[:2]
    title_multiline = "\n".join(lines)

    if len(lines) == 1:
        title_y = 55
        username_y = 110
        flag_y = 126
    else:
        title_y = 25
        username_y = 145
        flag_y = 162

    draw.text((block_left, title_y), title_multiline, font=font_bold_italic_med, fill=(200, 200, 200), spacing=14)

    draw.text((block_left, username_y), username, font=font_black_big, fill="white")
    bbox = draw.textbbox((block_left, username_y), username, font=font_black_big)
    text_width = bbox[2] - bbox[0]

    flag_ratio = flag_img.width / flag_img.height
    flag_height = 50 
    flag_width = int(flag_height * flag_ratio)
    flag_img = flag_img.resize((flag_width, flag_height))

    mask = Image.new("L", (flag_width, flag_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = 12 
    mask_draw.rounded_rectangle((0, 0, flag_width, flag_height), radius=radius, fill=255)

    card.paste(flag_img, (block_left + text_width + 15, flag_y), mask)

    size = 444
    avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
    card.paste(avatar, (52, 302), avatar)

    x0, y0 = 535, 337

    block_spacing = 60
    line_spacing = 120
    skill_offset = 20
    total_ox = 80
    total_oy = 35

    # ACCURACY
    draw.text((x0, y0), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8), "ACCURACY", font=font_light_italic_med, fill="white")
    accuracy_value = f"{accuracy:.2f}" 
    int_part, frac_part = accuracy_value.split(".") 
    draw.text((x0 + 6, y0 + 52), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + total_oy), f" ~ {acc_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    # AIM
    draw.text((x0, y0 + line_spacing + block_spacing), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8 + line_spacing + block_spacing), "AIM", font=font_light_italic_med, fill="white")
    aim_value = f"{aim:.2f}"
    int_part, frac_part = aim_value.split(".")
    draw.text((x0 + 6, y0 + 52 + line_spacing + block_spacing), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52 + line_spacing), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52 + line_spacing + block_spacing), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + line_spacing + block_spacing + total_oy), f" ~ {aim_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    # SPEED
    draw.text((x0, y0 + 2 * line_spacing+ block_spacing * 2), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8 + 2 * line_spacing+ block_spacing * 2), "SPEED", font=font_light_italic_med, fill="white")
    speed_value = f"{speed:.2f}"
    int_part, frac_part = speed_value.split(".")
    draw.text((x0 + 6, y0 + 52 + 2 * line_spacing+ block_spacing * 2), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52 + 2 * line_spacing), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52 + 2 * line_spacing+ block_spacing * 2), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + 2 * line_spacing+ block_spacing * 2 + total_oy), f" ~ {speed_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    x0, y0 = 73, 770
    x_block = x0 + 300
    block_width = 122

    draw.text((x0, y0), "Global", font=font_medium_italic_med, fill="white")
    draw.text((x0, y0 + 33), f"#{global_rank}", font=font_bold_small, fill="white")
    
    country_text = f"#{country_rank}"

    bbox = draw.textbbox((0, 0), country_text, font=font_bold_small)
    text_width = bbox[2] - bbox[0]

    x_text = x_block + block_width - text_width

    draw.text((x_block, y0), "Country", font=font_light_italic_small, fill="white")
    draw.text((x_text, y0 + 34), country_text, font=font_bold_small_2, fill="white")

    x0, y0 = 87, 915
    level_value = level
    level_int = int(level_value)           
    level_frac = level_value - level_int   

    draw.text((x0, y0), "Level", font=font_light_italic_small_2, fill="white")
    bbox = draw.textbbox((x0, y0), "Level", font=font_light_italic_small_2)
    width_text = bbox[2] - bbox[0]

    draw.text((x0 + width_text + 12, y0), f"{level_int}", 
            font=font_bold_italic_small, fill="white")
    bbox_num = draw.textbbox((x0 + width_text + 12, y0), f"{level_int}", font=font_bold_italic_small)
    width_num = bbox_num[2] - bbox_num[0]

    bar_left = x0 + width_text + width_num + 30   
    bar_right = x0 + 806                         
    bar_width = bar_right - bar_left

    bar_y0 = y0 + 15
    bar_height = 8
    bar_y1 = bar_y0 + bar_height
    radius = bar_height // 1

    draw.line(
        (bar_left, bar_y0 + bar_height // 2, bar_right, bar_y0 + bar_height // 2),
        fill="white", width=2
    )

    fill_len = int(bar_width * level_frac)

    if fill_len > 0:
        draw.rounded_rectangle(
            [bar_left, bar_y0, bar_left + fill_len, bar_y1],
            radius=radius,
            fill="white"
        )

    x0, y0 = 87, 894
    medals_max = 339
    medals_value = medals
    medals_percent = medals_value / medals_max
    medals_progress = int(medals_percent * 100)
       
    color_0 = (161, 190, 206)
    color_40 = (255, 140, 104)
    color_60 = (236, 85, 110)
    color_80 = (182, 106, 237)
    color_90 = (106, 237, 255)
    color_95 = (93, 89, 249)

    progress_color = color_0
   
    if medals_progress < 40:
        progress_color = color_0 
    elif medals_progress < 60:
        progress_color = color_40 
    elif medals_progress < 80:
        progress_color = color_60
    elif medals_progress < 90:
        progress_color = color_80
    elif medals_progress < 95:
        progress_color = color_90
    else: progress_color = color_95

    block_right = x0 + 808  

    text_label = "Medals"
    draw.text((x0, y0 + 60), text_label, font=font_light_italic_small_2, fill="white")

    bbox_label = draw.textbbox((x0, y0 + 60), text_label, font=font_light_italic_small_2)
    width_label = bbox_label[2] - bbox_label[0]

    draw.text((x0 + width_label + 12, y0 + 60), f"{medals_progress}%", 
            font=font_bold_italic_small, fill=progress_color)

    bbox_num = draw.textbbox((x0 + width_label + 12, y0 + 60), 
                            f"{medals_progress}%", 
                            font=font_bold_italic_small)
    width_num = bbox_num[2] - bbox_num[0]

    bar_left = x0 + width_label + width_num + 30 

    current_text = str(medals_value)
    max_text = str(medals_max)
    right_text = f"{current_text}/{max_text}"

    bbox_right = draw.textbbox((0, 0), right_text, font=font_regular_nano)
    width_right = bbox_right[2] - bbox_right[0]

    text_x = block_right - width_right
    text_y = y0 + 65

    draw.text((text_x, text_y), current_text, font=font_bold_nano, fill="white")
    bbox_cur = draw.textbbox((text_x, text_y), current_text, font=font_bold_nano)
    cur_width = bbox_cur[2] - bbox_cur[0]

    draw.text((text_x + cur_width, text_y), f"/{max_text}", 
            font=font_regular_nano, fill="white")

    bar_right = text_x - 15
    bar_width = bar_right - bar_left

    bar_y0 = y0 + 75
    bar_height = 8
    bar_y1 = bar_y0 + bar_height
    radius = bar_height // 1
    
    line_y = bar_y0 + bar_height // 2

    zone1_end = bar_left + round(bar_width * 0.39)
    zone2_end = bar_left + round(bar_width * 0.59)
    zone3_end = bar_left + round(bar_width * 0.79)
    zone4_end = bar_left + round(bar_width * 0.89)
    zone5_end = bar_left + round(bar_width * 0.94)
    zone6_end = bar_right

    draw.line((bar_left, line_y, zone1_end, line_y),    fill=color_0, width=2)
    draw.line((zone1_end, line_y, zone2_end, line_y), fill=color_40, width=2)
    draw.line((zone2_end, line_y, zone3_end, line_y), fill=color_60, width=2)
    draw.line((zone3_end, line_y, zone4_end, line_y), fill=color_80, width=2)
    draw.line((zone4_end, line_y, zone5_end, line_y), fill=color_90, width=2)
    draw.line((zone5_end, line_y, zone6_end, line_y), fill=color_95, width=2)

    fill_len = int(bar_width * medals_percent)
    if fill_len > 0:
        draw.rounded_rectangle(
            [bar_left, bar_y0, bar_left + fill_len, bar_y1],
            radius=radius,
            fill=progress_color
        )

    bot_first, bot_second = "Fujiyaosu", "Bot"
    today = date.today().isoformat()
    draw.text((220, 1140), bot_first, font=font_black_small, fill="white")
    bbox = draw.textbbox((0, 0), bot_first, font=font_black_small)
    text_width = bbox[2] - bbox[0]
    draw.text((222+text_width, 1140), bot_second, font=font_thin_small, fill="white")

    draw.text((700, 1140), today, font=font_light_italic_big, fill="white")

    card.convert("RGB").save(output) 
    print(f"Saved {output}")
    return output

async def button_handler_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    author_id = message_authors.get(query.message.message_id)
    if author_id != query.from_user.id:
        await query.answer("❌ Только автор команды может нажимать эти кнопки", show_alert=True)
        return

    if data == "profile":
        await profile(update, context)
    elif data == "card":
        await card(update, context)
    elif data == "noop":
        await query.answer("Уже здесь ✅", show_alert=False)
async def create_profile_image(user_data: dict, best_pp: str) -> str | None:
    final_w, final_h = 1000, 400

    cover_url = user_data.get("cover_url")
    if cover_url:
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(cover_url, timeout=timeout) as resp:
                    if resp.status == 200:
                        bg_bytes = await resp.read()
                        banner = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
                        bw, bh = banner.size
                        target_ratio = final_w / final_h
                        banner_ratio = bw / bh
                        if banner_ratio > target_ratio:
                            new_w = int(bh * target_ratio)
                            left = (bw - new_w) // 2
                            banner = banner.crop((left, 0, left + new_w, bh))
                        else:
                            new_h = int(bw / target_ratio)
                            top = (bh - new_h) // 2
                            banner = banner.crop((0, top, bw, top + new_h))
                        banner = banner.resize((final_w, final_h), Image.LANCZOS)
                    else:
                        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                print(f"Failed to load cover_url: {e}")
                banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
    else:
        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))

    draw = ImageDraw.Draw(banner)

    try:
        font_name = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 60)
        font_stats = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 28)
        font_small = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 24)
    except IOError:
        font_name = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def draw_text_with_shadow_3(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw_obj, position, text, font, fill=(255, 255, 255, 255),
                              shadowcolor=(0, 0, 0, 255), shadow_offset=3):
        x, y = position
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                if dx == 0 and dy == 0:
                    continue
                draw_obj.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
        draw_obj.text((x, y), text, font=font, fill=fill)

    avatar_top = 35
    async with aiohttp.ClientSession() as session:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(user_data["avatar_url"], timeout=timeout) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_img = avatar_img.resize((200, 200))
                    mask = Image.new("L", avatar_img.size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    corner_radius = 20 
                    mask_draw.rounded_rectangle((0, 0, 200, 200), radius=corner_radius, fill=255)
                    avatar_img.putalpha(mask)
                    shadow = Image.new("RGBA", avatar_img.size, (0, 0, 0, 180))
                    banner.paste(shadow, (50 + 5, avatar_top + 5), mask)
                    banner.paste(avatar_img, (50, avatar_top), avatar_img)
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"Failed to load avatar_url: {e}")

    try:
        short_name = ""
        team_flag_url = user_data.get("team", {}).get("flag_url")
        if team_flag_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(team_flag_url) as resp:
                    if resp.status == 200:
                        flag_bytes = await resp.read()
                        flag_img = Image.open(io.BytesIO(flag_bytes)).convert("RGBA")
                        fw, fh = flag_img.size
                        scale_factor = 200 / fw  
                        new_w = int(fw * scale_factor)
                        new_h = int(fh * scale_factor)
                        flag_img = flag_img.resize((new_w, new_h), Image.LANCZOS)
                        
                        shadow = Image.new("RGBA", flag_img.size, (0, 0, 0, 180))
                        
                        flag_alpha = flag_img.split()[3]

                        flag_y = avatar_top + 200 + 10
                        shadow_offset = (5, 5) 

                        
                        banner.paste(shadow, (50 + shadow_offset[0], flag_y + shadow_offset[1]), flag_alpha)
                        
                        banner.paste(flag_img, (50, flag_y), flag_img)

        short_name = "team tag:  " + user_data.get("team", {}).get("short_name", "")
        if short_name:
            flag_y_bottom = avatar_top + 200 + 15 + (new_h if team_flag_url else 0)
            draw_text_with_shadow_3(draw, (50, flag_y_bottom + 5), short_name, font_stats, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))
    except Exception as e: 
        print(e)
        
    username = user_data["username"]
    draw_text_with_shadow(draw, (280, 40), username, font_name)

    stats = user_data["statistics"]
    country_rank = stats.get("rank", {}).get("country", None)

    def hue_to_rgba(hue, saturation=1.0, lightness=0.5, alpha=255):
        if hue is None:
            hue = 349
        h = (hue % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)
        return (int(r * 255), int(g * 255), int(b * 255), alpha)

    def draw_text_with_shadow_2(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        draw.text((x + 1, y + 1), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fill)

    def draw_stat_line(draw, pos, key_text, value_text, font_key, font_value,
                    key_fill, key_shadow, value_fill, value_shadow, gap=8):
        x, y = pos

        draw_text_with_shadow(draw, (x, y), key_text, font_key, fill=key_fill, shadowcolor=key_shadow)

        bbox = draw.textbbox((x, y), key_text, font=font_key)
        key_w = bbox[2] - bbox[0]

        draw_text_with_shadow(draw, (x + key_w + gap, y), value_text, font_value, fill=value_fill, shadowcolor=value_shadow)

    stat_lines = [
        f"PP: {round(stats.get('pp', 0), 2)}",
        f"Country Rank: #{country_rank}" if country_rank else "Country Rank: N/A",
        f"Accuracy: {round(stats.get('hit_accuracy', 0), 2)}%",
        f"Playcount: {stats.get('play_count', 0):,}",
        f"Max Combo: {stats.get('maximum_combo', 0):,}",
        f"Playtime: {stats.get('play_time', 0) // 3600}h",
        f"Hits/Play: {round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)}",
        f" ",
        f" ",
        f"Max PP: {best_pp}",       
        f"Replays Watched: {stats.get('replays_watched_by_others', 0):,}", 
        
    ]

    profile_hue = user_data.get("profile_hue", 211)
    glow_color = hue_to_rgba(profile_hue, saturation=1, lightness=0.5, alpha=180)

    overlay_x, overlay_y = 270, 106
    overlay_w, overlay_h = 680, 240
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, 190))
    banner.paste(overlay, (overlay_x, overlay_y), overlay)

    col_gap = 340
    left_x, right_x = 280, 280 + col_gap
    y_start = 120

    for i, line in enumerate(stat_lines):
        col = i % 2
        row = i // 2
        x_pos = left_x if col == 0 else right_x
        y_pos = y_start + row * 32

        if ": " in line:
            key_text, value_text = line.split(": ", 1)
            key_text += ":"
        else:
            key_text, value_text = line, ""

        draw_stat_line(
            draw, (x_pos, y_pos),
            key_text, value_text,
            font_stats, font_stats,
            key_fill=(255, 255, 255, 220), key_shadow=(0, 0, 0, 180),
            value_fill=glow_color, value_shadow=(0, 255, 255, 180),
            gap=8
        )

    lvl_current = stats.get("level", {}).get("current", 0)
    lvl_progress = stats.get("level", {}).get("progress", 0)
    bar_x, bar_y = 280, final_h - 35
    bar_width, bar_height = 480, 15
    
    shadow_offset = (10, 10)
    shadow_color = (0, 0, 0, 200)
    shadow_radius = 35  

    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_draw.rounded_rectangle(
        [bar_x + shadow_offset[0], bar_y + shadow_offset[1], bar_x + bar_width + shadow_offset[0], bar_y + bar_height + shadow_offset[1]],
        radius=12,
        fill=shadow_color
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_radius))

    banner = Image.alpha_composite(banner, shadow_layer)

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                        radius=12, fill=(60, 60, 60, 200))
    fill_width = int(bar_width * (lvl_progress / 100))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                        radius=12, fill=(glow_color))
    
    text = f"Level {lvl_current} ({lvl_progress}%)"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = bar_x + bar_width + 10 
    text_y = bar_y + (bar_height - text_h) // 2

    draw_text_with_shadow_2(draw, (text_x, text_y), text, font_small, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))

    def draw_neon_glow(base_img, points, glow_color, glow_width=15, blur_radius=10):
        glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        glow_draw.line(points, fill=glow_color, width=glow_width, joint="curve")

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))

        base_img.alpha_composite(glow_layer)

    def draw_gradient_line(draw, points, start_color, end_color, width=3):
        n = len(points)
        for i in range(n - 1):
            t = i / (n - 2) if n > 2 else 0
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            a = int(start_color[3] + (end_color[3] - start_color[3]) * t)

            color = (r, g, b, a)
            draw.line([points[i], points[i+1]], fill=color, width=width, joint="curve")

    extra_height = 200
    new_banner = Image.new("RGBA", (banner.width, banner.height + extra_height), (30, 30, 30, 255))
    new_banner.paste(banner, (0, 0))
    banner = new_banner
    draw = ImageDraw.Draw(banner)

    background_img = Image.open(GRAPH_PNG).convert("RGBA")

    banner.paste(background_img, (0, 400), background_img) 


    rank_history = user_data.get("rank_history", {}).get("data")
    if rank_history:
        graph_x = 50
        graph_y = banner.height - extra_height + 20
        graph_width = banner.width - 100
        graph_height = extra_height - 40

        min_rank = min(rank_history)
        max_rank = max(rank_history)
        rank_range = max_rank - min_rank if max_rank != min_rank else 1

        points = []
        for i, rank in enumerate(rank_history):
            x = graph_x + (i / (len(rank_history) - 1)) * graph_width
            y = graph_y + ((rank - min_rank) / rank_range) * graph_height

            points.append((x, y))
        draw_neon_glow(banner, points, glow_color, glow_width=15, blur_radius=15)

        start_color = (255, 255, 255, 255)
        end_color = glow_color
        draw_gradient_line(draw, points, start_color, end_color, width=3)

        draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], outline=(150, 150, 150, 255), width=1)

    points = []
    for i, rank in enumerate(rank_history):
        x = graph_x + (i / (len(rank_history) - 1)) * graph_width
        y = graph_y + graph_height - ((rank - min_rank) / rank_range) * graph_height
        points.append((x, y))

    # ...

    rank_text = f"#{stats.get('global_rank'):,}" if stats.get("global_rank") else "Global Rank: N/A"
    bbox = draw.textbbox((0, 0), rank_text, font=font_name)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    last_point_x, last_point_y = points[-1]
    mid_y = graph_y + graph_height / 2
    padding = 5

    text_x = graph_x + graph_width - text_w 

    if last_point_y > mid_y:
        text_y = max(last_point_y - text_h - padding, graph_y)
    else:
        text_y = min(last_point_y + padding, graph_y + graph_height - text_h)

    draw_text_with_shadow(
        draw,
        (text_x, text_y),
        rank_text,
        font=font_name,
        fill=(255, 255, 255, 200),
        shadowcolor=(0, 0, 0, 180)
    )

    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    banner.save(tmp_file.name, "PNG")
    tmp_file.close()
    return tmp_file.name

#pc cmd TODO add single arg 
async def start_compare_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(compare_profile(update, context, user_request))
async def compare_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="pc",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    
    MAX_ATTEMPTS = 3  
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            temp_message = await update.message.reply_text(f"`Загрузочка... `{attempt}/{MAX_ATTEMPTS}", parse_mode="Markdown") 
            break
        except Exception as e:
            print(e)
            return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
    
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Загрузочка... {attempt}/{MAX_ATTEMPTS}`", 
                    parse_mode="Markdown")

            args_text = " ".join(context.args)

            if args_text.count("#") == 1:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Ошибка: найден только один #. Должно быть либо 0, либо 2.`",
                    parse_mode="Markdown"
                )
                return
            elif args_text.count("#") == 2:
                parts = args_text.split("#")
                username1 = parts[1].strip()
                username2 = parts[2].strip()
            else:
                parts = args_text.split()
                if len(parts) != 2:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=(
                            "Использование: `/pc <ник1> <ник2>`\n\n"
                            "Пример: `/pc Fujiya Vaxei`\n"
                            "Или с пробелами: `/pc #Fujiya #cs Pro 2014`"
                        ),
                        parse_mode="Markdown"
                    )
                    return
                username1, username2 = parts[0], parts[1]
            
            token = await get_osu_token()
            async def fetch_data(name):
                try:
                    user_data = await asyncio.wait_for(get_user_profile(name, token=token), timeout=10)
                    user_id = user_data["id"]
                    best_pp = await asyncio.wait_for(get_top_100_scores(name, token, user_id), timeout=10)
                    return user_data, best_pp
                except:
                    return None, None

            user1, top1 = await fetch_data(username1)
            user2, top2 = await fetch_data(username2)

            if not user1 or not user2:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Что-то пошло не так...`",
                    parse_mode="Markdown"
                )
                return
           
            p1 = format_stats(user1, top1)
            p2 = format_stats(user2, top2)

            header, sep = make_header(p1['name'], p2['name'])
            table = [header, sep]

            table.append(row(p1['rank'], "Rank", p2['rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['peak_rank'], "Peak rank", p2['peak_rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['pp'], "PP", p2['pp'], higher_is_better=True, suffix="pp", fmt="{:,.0f}"))
            table.append(row(p1['acc'], "Accuracy", p2['acc'], higher_is_better=True, suffix="%", fmt="{:,.2f}"))
            table.append(row(p1['level'], "Level", p2['level'], higher_is_better=True, fmt="{:.2f}"))
            table.append(row(p1['hours'], "Playtime", p2['hours'], higher_is_better=True, suffix="hrs", fmt="{:,}"))
            table.append(row(p1['playcount'], "Playcount", p2['playcount'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_count'], "PC peak", p2['max_count'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['maps'], "Maps played", p2['maps'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['ranked_score']/1e9, "Ranked score", p2['ranked_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_score']/1e9, "Total score", p2['total_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_hits'], "Total hits", p2['total_hits'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['hpp'], "Hits/play", p2['hpp'], higher_is_better=True, fmt="{:,.2f}"))
            table.append(row(p1['ss'], "SS count", p2['ss'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['s'], "S count", p2['s'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['a'], "A count", p2['a'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_combo'], "Max Combo", p2['max_combo'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['medals'], "Medals", p2['medals'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['top1_pp'], "Top1 PP", p2['top1_pp'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_diff'], "PP spread", p2['pp_diff'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_avg_all'], "Avg PP", p2['pp_avg_all'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_pp_per_month'], "PP per month", p2['avg_pp_per_month'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_count_per_month'], "PC per month", p2['avg_count_per_month'], higher_is_better=True, fmt="{:,.0f}"))
            table.append(row(p1['join_date'], "Join date", p2['join_date'], higher_is_better=False, is_date=True))
            table.append(row(p1['followers'], "Followers", p2['followers'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['mapping'], "Mapping subs", p2['mapping'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['posts'], "Forum posts", p2['posts'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['replays'], "Replays seen", p2['replays'], higher_is_better=True, fmt="{:,}"))

            text = "```\n" + "\n".join(table) + "\n```"

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=temp_message.message_id,
                text=text,
                parse_mode="Markdown"
            )
            return
        
        except Exception as e:
            print(f"Ошибка при pc (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
#fix cmd TODO add index arg 
async def start_recent_fix(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(recent_fix(update, context, user_request))
async def recent_fix(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="recent_fix",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_RECENT_FIX_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RECENT_FIX_COMMAND} секунд"
        )
    if not can_run:
        return

    try:
        uid = update.effective_user.id
        saved_name = await auth.check_osu_verified(str(uid))

        if context.args:
            username = " ".join(context.args)
        elif saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/fix Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
     
        text = "`загрузка...`"
        
        loading_msg = await try_send(update.message.reply_text, text, parse_mode="Markdown")

        token = await get_osu_token()
        scores = await get_user_scores(username, token, limit=1)

        if not scores:
            await safe_send_message(update, text="❌ Нет последних игр", parse_mode="Markdown")
            await loading_msg.delete()
            return

        score = scores[0]
        
        msg = await try_send(send_score_fix, update, score, uid, token)
        await loading_msg.delete()

      
        
    except Exception:
        traceback.print_exc()
async def send_score_fix(update, score, user_id, token:str = None):    
    
    path, base_values = await beatmap(score['beatmap']['id'])    
    score_stats = score.get("score_stats", score.get("statistics")) 

    base_ar = score.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = score.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = score.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = score.get("DA_values", {}).get("drain_rate", base_values["hp"])          
    
    #neko API 
    payload = {
        "map_path": str(score['beatmap']['id']), 
        
        "n300": score_stats.get("count_300", None),
        "n100": score_stats.get("count_100", None),
        "n50": score_stats.get("count_50", None),
        "misses": int(score['count_miss']),                   
        
        "mods": str(score.get("mods", 0)), 
        "combo": int(score['max_combo']),      
        "accuracy": float(score['accuracy']*100),    
        
        "lazer": bool(score.get('lazer', False)),          
        "clock_rate": float(score.get('speed_multiplier') or 1.0),  

        "custom_ar": float(base_ar),
        "custom_cs": float(base_cs),
        "custom_hp": float(base_hp),
        "custom_od": float(base_od),
    }

    try:
        pp_data = await localapi.get_score_pp_neko_api(payload)

        pp = pp_data.get("pp")
        max_pp = pp_data.get("no_choke_pp")
        perfect_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        perfect_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

    except Exception as e:
        print(f"neko API failed: {e}")
    
    
    mods_str = score.get("mods", "")
    mods_text = normalize_no_plus(mods_str)
    try:
        best_pp = await asyncio.wait_for(get_top_100_scores(score['user']['username'], token, score['user']['id']), timeout=10, )        
    except:
        return

    live_raw_pp = calculate_weighted_pp(best_pp, bonus_pp=0)
    map_pp = float(f"{max_pp:.3f}")

    try:
        pos, new_best_pp  = insert_pp(best_pp, map_pp, '')
    except:
        pos = None

    username = score['user']['username']
    total_pp, global_rank, country_rank, country_code = score['total_pp'], score['global_rank'], score['country_rank'], score['country_code']
    pp_text = f"{total_pp}"
    country_rank_text = (
        f"  {country_code}#{country_rank:,})"
    )
    rank_text = f"{username}: {pp_text}pp (#{global_rank}{country_rank_text}"
    country_flag = country_code_to_flag(country_code)
    user_link = f'{country_flag} <b>{rank_text}</b>'  

    pp_int, pp_frac = str(f"{pp:.2f}").split(".")
    max_pp_int, max_pp_frac = str(f"{max_pp:.2f}").split(".")
    
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   

    
    if pos is not None and pos<101:
        live_pp = total_pp
        bonus =  float(live_pp) - float(live_raw_pp)
        if bonus < 0: bonus = 0

        new_total = calculate_weighted_pp(new_best_pp, bonus)
        best_text =(
            f"{TR['r_fix_it_would'][lang_code]}<b>#{pos+1}</b>{TR['r_fix_in_top_100'][lang_code]}<b>{new_total:.2f}pp</b>."
        )    
    else:
        best_text =(
            f"\n{TR['r_fix_top100'][lang_code]}."
        ) 

    caption = (
        f"{user_link}\n\n"
        f'{mods_text} <b>FC</b>{TR["r_fix_improve"][lang_code]}<a href="{score["url"]}">{TR["r_fix_the_score"][lang_code]}</a>'
        f"{TR['r_fix_from'][lang_code]}<u>{pp_int}</u>.{pp_frac} "
        f"{TR['r_fix_to'][lang_code]}<b><u>{max_pp_int}</u>.{max_pp_frac}рр</b>.{best_text}"
        f"\n⠀"
    )        
    
    return await update.message.reply_text(text=caption, parse_mode="HTML")

#beatmaps cmd TODO add watch another ppl arg 
async def beatmaps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    can_run = await check_user_cooldown(
            command_name="beatmaps",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return      

    caller_id = update.effective_user.id
    msg, reply_markup = await build_beatmaps_text(caller_id)

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
async def fetch_beatmap_data(beatmap_url, cache_expire_sec=3600, retries=3, timeout_sec=10):    
    beatmap_id = beatmap_url.rstrip("/").split("/")[-1]
    cache_path = get_stats_cache_path(beatmap_id)

    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        if time.time() - mtime < cache_expire_sec:
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_sec)) as session:
                async with session.get(f"https://osu.ppy.sh/beatmaps/{beatmap_id}") as resp:
                    if resp.status == 200:
                        html_text = await resp.text()
                        tree = lxml.html.fromstring(html_text)
                        script = tree.xpath('//script[@id="json-beatmapset"]/text()')

                        result = {
                            "related_tags": [],
                            "tags": [],
                            "genre": None,
                            "language": None,
                            "artist": None
                        }

                        if script:
                            try:
                                data = json.loads(script[0])
                                
                                related_tags = data.get("related_tags", [])
                                result["related_tags"] = [tag.get("name") for tag in related_tags if "name" in tag]

                                tags_str = data.get("tags", "")
                                result["tags"] = tags_str.split() if tags_str else []

                                genre = data.get("genre")
                                if genre and "name" in genre:
                                    result["genre"] = genre["name"]

                                language = data.get("language")
                                if language and "name" in language:
                                    result["language"] = language["name"]

                                artist = data.get("artist")
                                if isinstance(artist, dict) and "name" in artist:
                                    result["artist"] = artist["name"]
                                elif isinstance(artist, str):
                                    result["artist"] = artist


                                with open(cache_path, "w", encoding="utf-8") as f:
                                    json.dump(result, f, ensure_ascii=False)
                            except json.JSONDecodeError:
                                pass

                        return result
                    else:
                        print(f"Attempt {attempt}: Status {resp.status} for beatmap {beatmap_id}")
        except Exception as e:
            print(f"Attempt {attempt}: Error fetching beatmap {beatmap_id}: {e}")
            await asyncio.sleep(1)
    return None
async def beatmaps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.username
    action, owner_id = query.data.split(":")
    owner_id = int(owner_id)

    if action == "beatmaps_refresh":
        if not os.path.exists(FLAG_FILE):
            open(FLAG_FILE, "w").close()
            asyncio.create_task(worker())
            print("worker startup from query")

        msg, reply_markup = await build_beatmaps_text(owner_id)
        
        try:
            await query.edit_message_text(
                msg,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except BadRequest as e:
            if "Message is not modified" in str(e):
                await safe_query_answer(query,"🍉 Ничего нового...")
            else:
                raise
        return
    
    if user_id != owner_id:
        await safe_query_answer(query,"⛔ Чужая кнопка")
        return
    
    if action == "beatmaps_count_me":
        count_me_times = temp.load_json(COUNT_ME_FILE, default={})
        now = time.time()
        last_click = count_me_times.get(str(user_id), 0)

        if now - last_click < COOLDOWN_WEEK_SECONDS:
            remaining = COOLDOWN_WEEK_SECONDS - (now - last_click)
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            await safe_query_answer(query, f"⏳ Подождите ещё {days} д {hours} ч, прежде чем нажимать снова.")
            return        
        
        saved_name = await auth.check_osu_verified(str(update.effective_user.id))
                
        if saved_name is None:
            await safe_query_answer(query, "🚷 Сначала нужно сохранить имя /name...")     
            return       
        else:
            await safe_query_answer(query, "👍 Запуск... \nНажми кнопку ОБНОВИТЬ чтобы увидеть статус")

        count_me_times[str(user_id)] = now
        temp.save_json(COUNT_ME_FILE, count_me_times)

        try:            
            group_state = await check_group_status(user_id)

            if group_state == 'not_found':
                pass
            
            elif group_state == 'done':
                print('query recalculating existing user, deleting data...')
                await delete_done_file(user_id)
            
            else:
                raise ValueError("group_state == in_progress")   

            token = await get_osu_token()
            best_pp = await asyncio.wait_for(get_top_100_scores(saved_name, token=token), timeout=10)
            if best_pp is None:              
                if update and context:                                          
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Такого ника не существует...",
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 5))                
                raise ValueError("best_pp is None")
            
            most_played = await asyncio.wait_for(get_most_played(saved_name, token=token), timeout=10)
            if most_played is None:              
                if update and context:                                          
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Такого ника не существует...",
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 5))                
                raise ValueError("best_pp is None")
           
            for score in best_pp:
                await addtask(
                    url = score.get("beatmap_url"),
                    task = 'beatmap_data',
                    group_id = user_id
            )
            for map in most_played:
                await addtask(
                    url = map.get("beatmap_url"),
                    task = 'beatmap_data',
                    group_id = user_id
            )
        
        except Exception as e:
            print(f"query adding workers: {e}")

            if str(e) != "group_state == in_progress":
                try:
                    count_me_times = temp.load_json(COUNT_ME_FILE, default={})
                    if str(user_id) in count_me_times:
                        del count_me_times[str(user_id)]
                        temp.save_json(COUNT_ME_FILE, count_me_times)
                        print(f"Cooldown for user {user_id} removed due to error.")
                except Exception as ex:
                    print(f"Error while removing cooldown: {ex}")

        finally:
            print(f"query adding workers done")

           
    elif action.startswith("beatmaps_stats"):
        sub_action = action.replace("beatmaps_stats", "").strip("_") or "200"

        todo_file = os.path.join(GROUPS_DIR, f"{user_id}.todo")
        done_file = os.path.join(GROUPS_DIR, f"{user_id}.done")

        if os.path.exists(todo_file):
            await safe_query_answer(query, "⏳ Ещё не готово!!!!!!!")
            return
        elif not os.path.exists(done_file):
            await safe_query_answer(query, "🚷 Еще нет статистики, может быть нажать на звездочку?")
            return

        try:            
            
            def filter_tags(tags, blacklist):
                return [t for t in tags if t.lower() not in blacklist]

            def format_top(counter, title, top_n=9, max_bar_width=5):
                most_common = counter.most_common(top_n)
                other_count = sum(count for _, count in counter.items()) - sum(count for _, count in most_common)

                split_tags = [t[0].split("/", 1) + [t[1]] if "/" in t[0] else [t[0], "", t[1]] for t in most_common]

                max_first_len = max(len(first) for first, _, _ in split_tags + [("other", "", 0)])
                max_second_len = max(len(second) for _, second, _ in split_tags + [("","",0)])

                max_count = max(count for _, _, count in split_tags) if split_tags else 1

                lines = []
                for first, second, count in split_tags:
                    bar_len = int((count / max_count) * max_bar_width)
                    bar_len = max(bar_len, 1)
                    bar = "▇" * bar_len
                    lines.append(f"{first.ljust(max_first_len)}  {second.ljust(max_second_len)} {bar} {count}")

                lines.append(f"{'other'.ljust(max_first_len)}  {'':{max_second_len}} {other_count}")
                return lines

            with open(done_file, "r", encoding="utf-8") as f:
                beatmap_paths = [line.strip() for line in f if line.strip()]

            if sub_action == "1_100":
                beatmap_paths = beatmap_paths[:100]
                title_text = "🔹 top-100 pp" 
            elif sub_action == "101_200":
                beatmap_paths = beatmap_paths[100:200]                 
                title_text = "🔸 most played"  
            else:  
                beatmap_paths = beatmap_paths[:200]  
                title_text = "📊 200 карт"     

            related_tag_counter = Counter()
            tags_counter = Counter()
            genre_counter = Counter()
            language_counter = Counter()
            artist_counter = Counter()


            for path in beatmap_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as bf:
                        try:
                            data = json.load(bf)
                        except json.JSONDecodeError:
                            continue 

                        if isinstance(data, dict):
                            related_tags = data.get("related_tags", [])
                            related_tag_counter.update(related_tags)

                            TAGS_FILTER = {
                                "the","of", "to","a","no", "wa","tv",                               
                                "english", "japanese", "russian", "korean",                               
                                "version",
                                "featured", "artist",   
                                }
                            tags = data.get("tags", [])
                            if isinstance(tags, str):
                                tags = tags.split()
                            tags = filter_tags(tags, TAGS_FILTER)
                            tags_counter.update(tags)

                            genre = data.get("genre")
                            if genre:
                                genre_counter.update([genre])

                            language = data.get("language")
                            if language:
                                language_counter.update([language])

                            artist = data.get("artist")
                            if artist:
                                artist_counter.update([artist])

                        elif isinstance(data, list):
                            tags_counter.update(data)

            if not related_tag_counter and not tags_counter:
                await safe_query_answer(query, "⚠️ Нет тегов в картах.")
                return

            saved_name = await auth.check_osu_verified(str(update.effective_user.id))
            saved_name = html.escape(saved_name)

            related_lines = format_top(related_tag_counter, "related_tags")
            tags_lines = format_top(tags_counter, "обычные tags")
            artist_lines = format_top(artist_counter, "исполнители")

            all_lines = []
            all_lines.append(f"{title_text} 🏷 Юзертеги: {saved_name}") 
            all_lines.append("────────────────────────────")
            all_lines.extend(related_lines)
            all_lines.append("────────────────────────────")
            all_lines.append(f"🏷 Теги, добавленные маппером:")
            all_lines.extend(tags_lines)
            all_lines.append("────────────────────────────")
            all_lines.append(f"🏷 Топ исполнителей:")
            all_lines.extend(artist_lines)
            all_lines.append("────────────────────────────")

            top_genre = html.escape(genre_counter.most_common(1)[0][0]) if genre_counter else "—"
            top_language = html.escape(language_counter.most_common(1)[0][0]) if language_counter else "—"
            all_lines.append(f"✳️ Любимый жанр: {top_genre}")
            all_lines.append(f"🌐 Любимый язык: {top_language}")

            table_text = "<pre>" + html.escape("\n".join(all_lines)) + "</pre>"

            if update and context:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=update.callback_query.message.message_id,
                        text=table_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка редактирования сообщения: {e}")
        except Exception as e:
            print(f"Ошибка обработки beatmaps_stats: {e}")
            await safe_query_answer(query, f"❌ Произошла неизвестная ошибка. \n\n{e}")
async def worker():
    await asyncio.sleep(1)
    try:
        processed = 0

        while True:
            if not os.path.exists(QUEUE_FILE):
                break

            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                break

            task_line = lines[0]
            parts = task_line.split(" ")
            url, task, group_id = parts[0], parts[1], parts[2]

            skip_timeout = False 

            if task == "beatmap_data":
                file_id = url.split("/")[-1]
                out_file = os.path.join(STATS_BEATMAPS, f"{file_id}.json")

                if os.path.exists(out_file):
                    print(f"⏭️ Already exists: {out_file}, skipping download...")
                    skip_timeout = True
                else:
                    print(f"🔄 Loading: {url}")
                    data = await fetch_beatmap_data(url)
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"✅ Saved {out_file}")

            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                f.writelines(line + "\n" for line in lines[1:])

            processed += 1

            if processed % 25 == 0 or not lines[1:]:
                mark_group_progress()

            if os.path.exists(QUEUE_FILE) and lines[1:]:
                if skip_timeout:
                    print("⚡ Skipped timeout (cached file)")
                else:
                    await asyncio.sleep(URL_SCAN_TIMEOUT)

    except Exception as e:
        print(e)
        mark_group_progress() 
    finally:
        mark_group_progress()         
        if os.path.exists(FLAG_FILE):
            os.remove(FLAG_FILE)
        print("worker job done")
async def addtask(url, task, group_id):
    file_id = url.split("/")[-1]
    out_file = os.path.join(STATS_BEATMAPS, f"{file_id}.json")

    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url} {task} {group_id}\n")

    with open(os.path.join(GROUPS_DIR, f"{group_id}.todo"), "a", encoding="utf-8") as f:
        f.write(out_file + "\n")

    print(f"📌 Добавил задачу: {url} ({task}), группа {group_id}")

    if not os.path.exists(FLAG_FILE):
        open(FLAG_FILE, "w").close()
        asyncio.create_task(worker())
        print("▶️ Запустил воркер")
async def check_group_status(group_id: str) -> str:
    """
    Проверяет статус группы по group_id.
    Возвращает:
      - "not_found"  → если нет такого файла
      - "in_progress" → если есть .todo, но нет .done
      - "done"       → если есть .done
    """
    todo_path = os.path.join(GROUPS_DIR, f"{group_id}.todo")
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if not os.path.exists(todo_path) and not os.path.exists(done_path):
        return "not_found"
    elif os.path.exists(done_path):
        return "done"
    else:
        return "in_progress"
async def delete_done_file(group_id: str):
    """
    Удаляет файл группы с расширением .done, если он существует.
    """
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if os.path.exists(done_path):
        try:
            os.remove(done_path)
            print(f"✅ Файл {group_id}.done успешно удалён.")
        except Exception as e:
            print(f"❌ Ошибка при удалении файла {group_id}.done: {e}")
    else:
        print(f"⚠️ Файл {group_id}.done не найден.")

#simulate cmd
async def simulate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    topic_id = getattr(update.effective_message, "message_thread_id", None)

    message_text = update.message.text.strip()
    match = OSU_MAP_REGEX.search(message_text)

    if not match:        
        msg = await update.message.reply_text(
            "❌ Нужна ссылка на карту"
        )
        asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
        asyncio.create_task(delete_user_message(update, context, delay=4))
        return

    beatmap_id = match.group(1) if match.group(1) else match.group(2)

    if user_id in sessions_simulate:
        try:
            await context.bot.delete_message(chat_id=sessions_simulate[user_id]["chat_id"],
                                             message_id=sessions_simulate[user_id]["message_id"])
        except:
            pass
        del sessions_simulate[user_id]

    user_params = {k: v.copy() for k, v in PARAMS_TEMPLATE.items()}

    path, values = await beatmap(beatmap_id)
    stats = {
        "n300": None,
        "n100": None,
        "n50": None,
    }

    #neko API 
    payload = {
        "map_path": str(beatmap_id), 
        
        "n300": 0,
        "n100": 0,
        "n50": 0,
        "misses": 0,                   
        
        "mods": str(""), 
        "combo": int(0),      
        "accuracy": float(100),    
        
        "lazer": bool(True),          
        "clock_rate": float(1.0),  

        "custom_ar": values.get("ar"),
        "custom_cs": values.get("cs"),
        "custom_hp": values.get("hp"),
        "custom_od": values.get("od"),
    }

    try:
        pp_data = await localapi.get_map_stats_neko_api(payload)

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

        aim = pp_data.get("aim")
        acc = pp_data.get("acc")
        speed = pp_data.get("speed")

    except Exception as e:
        print(f"neko API failed: {e}")


    user_params["300"]["max"] = n300 
    user_params["300"]["default"] = n300
    user_params["100"]["max"] = n300
    user_params["50"]["max"] = n300
    user_params["мисс"]["max"] = n300

    sessions_simulate[user_id] = {
        "chat_id": chat_id,
        "message_id": None,
        "topic_id":topic_id,
        "params": {k: v.get("default", "❌ не задано") for k, v in user_params.items()},
        "waiting": None,
        "hint_id": None,
        "schema": user_params,
        "path": path,
        "beatmap": beatmap_id,
        "values": values,
        "map_combo": max_combo,
        "300_changed": False,
        "100_changed": False,
        "50_changed": False,
        "miss_changed": False,
        "max_hits": n300,
        "grade": str(calculate_rank(n300, n100, n50, expected_miss, True)),
        "aim":aim,
        "acc":acc,
        "speed":speed,
    }

    msg = await update.message.reply_text(format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss), 
                                          reply_markup=get_simulate_keyboard(user_id),
                                          parse_mode="Markdown" )
    sessions_simulate[user_id]["message_id"] = msg.message_id
def get_simulate_keyboard(user_id):
    schema = sessions_simulate[user_id]["schema"]
    keys = list(schema.keys())
    buttons = []

    for i in range(0, len(keys), 4):
        row = []
        for j in range(4):
            if i + j < len(keys):
                row.append(InlineKeyboardButton(keys[i + j], callback_data=f"simulate_{keys[i + j]}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("☑️", callback_data="simulate_close")])

    return InlineKeyboardMarkup(buttons)
def format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss):
    sess = sessions_simulate[user_id]
    schema = sess["schema"]

    text = "```\n"

    text += f"{'Ранк':<18}{'Точность':<12}\n"

    grade = sess["grade"]
    grade_text = grade + f' +{sess["params"].get("Моды")}'
    acc = sess["params"].get("Точность", "?")
    acc_text = f'{float(acc):.2f}% (CL)'
    combo = sess["params"].get("Комбо", max_combo)
    combo_text = f'{combo}x/{max_combo}x'

    text += f"{grade_text:<18}{acc_text:<12}\n\n"

    text += f"{'PP':<18}{'Hits':<12}\n"

    pp =  f"{pp:.1f}" if pp is not None else '?'
    pp_text = f"{pp}/{max_pp:.1f}PP"
    hits_text = "{"
    hits_text += f"{n300}/{n100}/{n50}/{expected_miss}"
    hits_text += "}"
    
    text += f"{pp_text:<18}{hits_text:<12}\n\n"

    aim, acc, speed = sess["aim"], sess["acc"], sess["speed"]
    skills_text = f"Aim:Acc:Speed"
    rate = f'{sess["params"].get("Скорость")}x'

    text += f"{skills_text:<22}{'Скорость':<8}\n"

    skills_text = f"{aim:.0f} : {acc:.0f} : {speed:.0f}"    
    text += f"{skills_text:<22}{rate:<8}\n"

    text += f""
    text += "```\n"

    return text
async def clear_s_chat(update, context, msg_chat_id, msg_message_id, delay_1, delay_2):
    asyncio.create_task(delete_user_message(update, context, delay=delay_1))
    asyncio.create_task(delete_message_after_delay(context, msg_chat_id, msg_message_id, delay_2))
async def simulate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    sess = sessions_simulate.get(user_id)

    if not sess or sess["message_id"] != query.message.message_id:
        return await safe_query_answer(query, "❌ Это меню не для вас")

    if query.data == "simulate_close":
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=sess["chat_id"],
                message_id=sess["message_id"],
                reply_markup=None
            )
        except:
            pass

        if sess.get("hint_id"):
            try:
                await context.bot.delete_message(chat_id=sess["chat_id"], message_id=sess["hint_id"])
            except:
                pass

        del sessions_simulate[user_id]
        return await safe_query_answer(query, "✅ Меню закрыто")

    schema = sess["schema"]
    param_name = query.data.replace("simulate_", "", 1)
    if param_name not in schema:
        return await safe_query_answer(query, "❌ Неизвестный параметр")

    await safe_query_answer(query, text=None, show_alert=False)
    sess["waiting"] = param_name

    if sess.get("hint_id"):
        try:
            await context.bot.delete_message(chat_id=sess["chat_id"], message_id=sess["hint_id"])
        except:
            pass

    hint_msg = await context.bot.send_message(
        sess["chat_id"],
        message_thread_id=sess["topic_id"],
        text=f"👉 @{query.from_user.username or query.from_user.first_name}, {schema[param_name]['msg']}"
    )
    sess["hint_id"] = hint_msg.message_id
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
            pp_data = await localapi.get_map_stats_neko_api(payload)

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
async def start_simulate_text_handler(update, context):
    try:
        asyncio.create_task(simulate_text_handler(update, context))            
    except Exception as e: print(e)
def calc_accuracy(n300, n100, n50, miss):
    total_hits = n300 + n100 + n50 + miss
    if total_hits == 0:
        return 0.0
    acc = (300 * n300 + 100 * n100 + 50 * n50) / (300 * total_hits)
    return acc * 100 
def update_hits(sess, param_name, new_value):
    priority = ["300", "100", "50", "мисс"]
    key_map = {"300k": "300", "100k": "100", "50k": "50", "miss": "мисс"}
    real_name = key_map.get(param_name, param_name)
    print("update_hits called with:", param_name, "->", key_map.get(param_name))
    
    changed_flags = {
        "300": sess["300_changed"],
        "100": sess["100_changed"],
        "50": sess["50_changed"],
        "мисс": sess["miss_changed"],
    }
    values = {k: int(sess["params"][k]) for k in priority}

    fixed = {k: v for k, v in values.items() if changed_flags[k] and v > 0}
    free = [k for k in priority if not changed_flags[k] or values[k] == 0]

    if len(fixed) >= 3 and not changed_flags[real_name]:
        return

    values[real_name] = int(new_value)
    if real_name == "300":
        sess["300_changed"] = new_value != 0
    elif real_name == "100":
        sess["100_changed"] = new_value != 0
    elif real_name == "50":
        sess["50_changed"] = new_value != 0
    elif real_name == "мисс":
        sess["miss_changed"] = new_value != 0

    changed_flags = {
        "300": sess["300_changed"],
        "100": sess["100_changed"],
        "50": sess["50_changed"],
        "мисс": sess["miss_changed"],
    }
    fixed = {k: v for k, v in values.items() if changed_flags[k] and v > 0}
    free = [k for k in priority if not changed_flags[k] or values[k] == 0]

    total = sess["max_hits"]
    sum_fixed = sum(fixed.values())
    remaining = max(0, total - sum_fixed)

    for k in priority:
        if k in free:
            values[k] = remaining
            break

    for k in priority:
        sess["params"][k] = str(values[k])
def calculate_rank(n300: int, n100: int, n50: int, miss: int, lazer: bool = True) -> str:
    n300 = int(n300 or 0)
    n100 = int(n100 or 0)
    n50 = int(n50 or 0)
    miss = int(miss or 0)
    total_hits = n300 + n100 + n50 + miss
    if total_hits == 0:
        return "D"

    if lazer:
        accuracy = (300*n300 + 100*n100 + 50*n50) / (300*total_hits) * 100
    else:
        accuracy = (n300 + n100*2/3 + n50*1/3) / total_hits * 100

    if miss == 0 and n300 == total_hits:
        rank = "SS"
    elif accuracy > 95:
        rank = "S"
    elif accuracy > 90:
        rank = "A"
    elif accuracy > 80:
        rank = "B"
    elif accuracy > 70:
        rank = "C"
    else:
        rank = "D"

    return rank

#settings cmd
async def settings_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = str(update.effective_user.id)
    name = str(update.effective_user.name)

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
  
    kb, text = await get_settings_kb(user_id, settings)

    await update.message.reply_text(
        f'{text} {name}',
        reply_markup=InlineKeyboardMarkup(kb)
    )
async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    name = str(query.from_user.name)
    action, owner_id = query.data.split(":")

    if user_id != owner_id:
        await safe_query_answer(query, "Чужая кнопка") 
        return

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = settings.get(str(user_id), {"lang": "ru", "notify": True, "rs_bg_render": False, "new_card": True})    

    if action == "settings_english":
        user_settings["lang"] = "en"
        await safe_query_answer(query) 

    elif action == "settings_russian":
        user_settings["lang"] = "ru"
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_yes":
        user_settings["rs_bg_render"] = True
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_no":
        user_settings["rs_bg_render"] = False
        await safe_query_answer(query) 

    elif action == "settings_new_card":
        user_settings["new_card"] = True
        await safe_query_answer(query) 

    elif action == "settings_old_card":
        user_settings["new_card"] = False
        await safe_query_answer(query) 

    elif action == "settings_ignore":
        await safe_query_answer(query) 

    settings[user_id] = user_settings
    temp.save_json(USER_SETTINGS_FILE, settings)

    kb, text = await get_settings_kb(user_id, settings)

    try:
        await query.edit_message_text(
            f'{text} {name}',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception as e:
        await query.answer()
async def get_settings_kb(user_id, user_data):
    

    user_settings = user_data.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   
    bg_code = user_settings.get("rs_bg_render", False) 
    new_card = user_settings.get("new_card", True) 

    
    if lang_code == "en":
        en_flag = "✅"
        ru_flag = ""
    else:
        en_flag = ""
        ru_flag = "✅"
    
    if bg_code:
        bg_y_flag = "✅"
        bg_n_flag = ""
    else:
        bg_y_flag = ""
        bg_n_flag = "✅"

    if new_card:
        new_card_flag = "✅"
        old_card_flag = ""
    else:
        new_card_flag = ""
        old_card_flag = "✅"

    keyboard = [
        [
            InlineKeyboardButton(
                f"🎨 {TR['settings_rs_title'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         f"{TR['settings_n_a'][lang_code]}",
        #         callback_data=f"settings_ignore:{user_id}"
        #     )
        # ],
        [
            InlineKeyboardButton(
                f"{TR['settings_yes'][lang_code]} {bg_y_flag}",
                callback_data=f"settings_rs_bg_yes:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['settings_no'][lang_code]} {bg_n_flag}",
                callback_data=f"settings_rs_bg_no:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"🖼 {TR['settings_card_title'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['settings_new'][lang_code]} {new_card_flag}",
                callback_data=f"settings_new_card:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['settings_old'][lang_code]} {old_card_flag}",
                callback_data=f"settings_old_card:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"🌐 {TR['lang'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['english'][lang_code]} {en_flag}",
                callback_data=f"settings_english:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['russian'][lang_code]} {ru_flag}",
                callback_data=f"settings_russian:{user_id}"
            )
        ]
    ]

    text = TR['settings_title'][lang_code]

    return keyboard, text
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)
    await safe_send_message(update, "https://myangelfujiya.ru/darkness/auth")

#all moderation
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await log_all_update(update)
        
        print(f"chat {update.effective_chat.id}, topic {getattr(update.effective_message, 'message_thread_id', None)}")

        try:
            text = update.message.text.strip()
            telegram_id = str(update.message.from_user.id)

            if re.fullmatch(r"[A-Z0-9]{6}", text):    
                username = await auth.verify_osu_user(text, telegram_id)

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

                                
            DICE_EMOJI = '🎲'
            SLOT_EMOJI = '🎰'
            BALL_EMOJI = '🏀'
            DART_EMOJI = '🎯'

            LUCKY_EMOJIS = {DICE_EMOJI, SLOT_EMOJI, BALL_EMOJI, DART_EMOJI}

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

            if not update.message or not update.message.text:
                return
        
            user_id = str(update.message.from_user.id)
            username = update.message.from_user.username or update.message.from_user.first_name
            text = update.message.text.lower()
            
            # positive_words = temp.load_text_list(POSITIVE_FILE)
            # negative_words = temp.load_text_list(NEGATIVE_FILE)
            
            # ratings = load_ratings()

            # if user_id not in ratings:
            #     ratings[user_id] = {"name": username, "rating": 0}
            # else:
            #     ratings[user_id]["name"] = username

            # if any(word in text for word in positive_words):
            #     ratings[user_id]["rating"] += 1
            # if any(word in text for word in negative_words):
            #     ratings[user_id]["rating"] -= 1
            # save_ratings(ratings)
    except: print(e)
async def start_check_reminders(update, context):
    asyncio.create_task(check_reminders(update, context))

async def check_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message.from_user:
        return

    username = update.effective_message.from_user.username
    if not username:
        return

    username_lower = username.lower()

    try:
        with open(REMINDERS_DATA_FILE, "r", encoding="utf-8") as f:
            reminders = json.load(f)
    except FileNotFoundError:
        reminders = []

    updated = False
    new_reminders = []

    for i, reminder in enumerate(reminders, start=1):
        message_lower = reminder["message"].lower()

        if f"@{username_lower}" in message_lower:

            reminder_datetime_str = f"{reminder['date']} {reminder['time']}"
            reminder_datetime = datetime.strptime(reminder_datetime_str, "%Y-%m-%d %H:%M")
            now = datetime.now()

            if now >= reminder_datetime:
                await update.effective_chat.send_message(reminder["message"])

                reminder["repeatCount"] -= 1

                if reminder["repeatCount"] > 0:
                    new_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                    new_time = now.strftime("%H:%M")
                    reminder["date"] = new_date
                    reminder["time"] = new_time
                    new_reminders.append(reminder)
              
                updated = True
            else:
                new_reminders.append(reminder)
        else:
            new_reminders.append(reminder)

    if updated:
        with open(REMINDERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_reminders, f, ensure_ascii=False, indent=2)

import string
def generate_unique_code(existing_codes, length=8):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in existing_codes:
            return code

async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    if update.effective_chat.type != "private":
        await update.effective_message.reply_text("Эта команда работает только в личном чате.")
        return

    user_id = str(update.effective_user.id)

    try:
        with open(REMINDERS_PW_FILE, "r", encoding="utf-8") as f:
            passwords = json.load(f)
    except FileNotFoundError:
        passwords = {}

    if user_id in passwords:
        # Если код уже есть, просто отправляем его
        code = passwords[user_id]
        await update.effective_message.reply_text(f"Твой пароль: `{code}` \n https://myangelfujiya.ru/darkness", parse_mode="Markdown")
        print(f"[DEBUG] Пользователь {user_id} запросил существующий код: {code}")
        return

    existing_codes = set(passwords.values())
    code = generate_unique_code(existing_codes)

    passwords[user_id] = code
    with open(REMINDERS_PW_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

    await update.effective_message.reply_text(f"Твой пароль: `{code}`", parse_mode="Markdown")
    print(f"[DEBUG] Создан новый код для пользователя {user_id}: {code}")

#non-cmd cmd
async def start_osu_link_handler(update, context):
    try:
        if await is_on_cooldown("start_osu_link_handler", COOLDOWN_LINKS_IN_CHAT):   
            print('start_osu_link_handler on cooldown')
            return
        else:
            flag = False
            flag = await osu_link_profile_handler(update, context)
            flag = await osu_link_score_handler(update, context)
            if flag:
                await update_cooldown("start_osu_link_handler")
    except Exception as e: print(e)
async def osu_link_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption
    if not text:
        return False

    match = OSU_USER_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]
    await start_profile(update, context)
    return True
async def osu_link_score_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption
    if not text: 
        return False

    match = OSU_SCORE_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]
    asyncio.create_task(score(update, context, False))
    return True
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE, requested_by_user = True):
    """Функция /score для показа одного конкретного скора по его ID"""
    user_id = str(update.effective_user.id)
    print('async def score')

    if requested_by_user:
        can_run = await check_user_cooldown(
            command_name="score",
            user_id=user_id,
            cooldown_seconds=COOLDOWN_RS_COMMAND,
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RS_COMMAND} секунд"
        )
        if not can_run:
            return

    if context.args:
        score_id = context.args[0]
    else:
        await safe_send_message(update, "⚠ Не указан ID скора", parse_mode="Markdown")
        return

    try:
        token = await get_osu_token()

        await get_score_by_id(score_id, token)

        cached_score = load_score_file(score_id)
        if not cached_score:
            await safe_send_message(update, "❌ Не удалось загрузить скор после кеша", parse_mode="Markdown")
            return

        final_score = cached_score["raw"]

        await send_score(update, final_score, user_id, user_id, user_id, is_recent=False)

    except Exception:
        traceback.print_exc()
        await safe_send_message(update, "❌ Ошибка при получении скора", parse_mode="Markdown")
async def get_score_by_id(score_id: str, token: str, timeout_sec: int = 10):
    """Получает один конкретный скор по его ID и кеширует его, включая enrich_score_lazer"""
    cached_entry = load_score_file(score_id)

    if cached_entry:
        final_score = cached_entry["raw"]

    else:
        async with aiohttp.ClientSession() as session:
            data = await get_score_page(session, score_id, score_id, no_check=True)

        if not data:
            return None  

        user_id = str(data["user"]["id"])
        additional_data = await get_osu_user_additional_data(user_id, "osu", token)

        cached_entry = {"raw": data, "processed": {}, "ready": False}
        save_score_file(score_id, cached_entry)

        async with aiohttp.ClientSession() as session:
            await enrich_score_lazer(session, user_id, score_id)

        cached_entry = load_score_file(score_id)
        raw = cached_entry["raw"]

        final_score = await process_score(raw, additional_data)

        cached_entry["raw"] = final_score
        cached_entry["ready"] = True
        save_score_file(score_id, cached_entry)

    return final_score


#testing zone
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="ping",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_DEV_COMMANDS} секунд"
        )
        if not can_run:
            return

        start = time.time()
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Pong!",
            message_thread_id=update.message.message_thread_id
        )
        end = time.time()
        latency = (end - start) * 1000 
        await msg.edit_text(f"🏓   {latency:.2f} ms")

    except Exception as e:
        print(f"Ошибка в команде /ping: {e}")
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="uptime",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_DEV_COMMANDS} секунд"
        )
        if not can_run:
            return

        current_time = time.time()
        uptime_seconds = int(current_time - START_TIME)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Uptime: {days}d {hours}h {minutes}m {seconds}s",
            message_thread_id=update.message.message_thread_id
        )

    except Exception as e:
        print(f"Ошибка в команде /uptime: {e}")
async def start_nochoke(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(nochoke(update, context, user_request))
async def nochoke(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="average_stats",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 1  

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    miss_limit = None
    args = context.args

    if args:
        # %N
        for arg in args:
            if arg.startswith("%") and arg[1:].isdigit():
                miss_limit = int(arg[1:])
                args.remove(arg)
                break
        username = " ".join(args) if args else saved_name
    else:
        username = saved_name

    if not username:
        text = (f"`Нужна помощь?`\n\n"
                f"Сохранить ник: */name*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n"
        )
        await safe_send_message(update, text, parse_mode="Markdown")
        return

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        text=f"`Загрузочка... (20 сек макс.)`\n\n"
                        f"Сохраненный ник: *{saved_name}*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет игрока или статистики...`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)            
            

            if isinstance(best_scores, list) and best_scores:
                live_raw_pp = calculate_weighted_pp(best_scores, bonus_pp=0)
                                
                stats = user_data["statistics"]
                live_pp = f"{stats.get('pp', 0):.2f}"
               
                bonus =  float(live_pp) - float(live_raw_pp)
                if bonus < 0: bonus = 0

                stars = []
                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    acc = (score.get("accuracy", 1.0) * 100)
                    combo = score.get("combo", 0.0)
                    pp = score.get("pp", 0.0)
                    mods_str = score.get("mods", "")     
                    path = results.get(score['beatmap_id'], None)
                    score_stats = score.get("score_stats")
                    lazer = score.get("lazer")   

                    misses = score.get("misses", 0)
                    if miss_limit is not None and misses > miss_limit:
                        new_pp = pp
                        max_combo = combo
                        stars = score.get("stars", 0.0)  
                    else:
                        #neko API 
                        payload = {
                            "map_path": str(score.get('beatmap_id', "0")), 
                            
                            "n300": int(score_stats.get("count_300", 0)),
                            "n100": int(score_stats.get("count_100", 0)),
                            "n50": int(score_stats.get("count_50", 0)),
                            "misses": int(misses),                   
                            
                            "mods": str(score.get("mods", 0)), 
                            "combo": int(score.get("combo", 0.0)),      
                            "accuracy": float(score.get("accuracy", 1.0) * 100),    
                            
                            "lazer": bool(score.get('lazer', False)),          
                            "clock_rate": float(score.get('speed_multiplier') or 1.0),  

                            "custom_ar": float(score.get('AR', 0.0)),
                            "custom_cs": float(score.get('CS', 0.0)),
                            "custom_hp": float(score.get('HP', 0.0)),
                            "custom_od": float(score.get('OD', 0.0)),
                        }

                        try:
                            pp_data = await localapi.get_score_pp_neko_api(payload)

                            _pp = pp_data.get("pp")
                            max_pp = pp_data.get("no_choke_pp")
                            perfect_pp = pp_data.get("perfect_pp")

                            stars = pp_data.get("star_rating")
                            max_combo = pp_data.get("perfect_combo")
                            expected_bpm = pp_data.get("expected_bpm")

                        except Exception as e:
                            print(f"neko API failed: {e}")                     
                                                

                    score["index"] = i + 1
                    score["pp_old"] = pp
                    score["pp_new"] = max_pp
                    score["stars"] = stars
                    score["combo_old"] = combo
                    score["combo_max"] = max_combo

                    
                  
                best_scores = sorted(
                    best_scores, 
                    key=lambda s: s.get("pp_new", 0), 
                    reverse=True
                )
                for i, score in enumerate(best_scores):
                    score["weight_percent"] = 0.95 ** i
                
                total_pp = 0
                for i, score in enumerate(best_scores):
                    weight = 0.95 ** i
                    total_pp += score.get("pp_new", 0) * weight
                new_total = total_pp + bonus

                best_scores = [s for s in best_scores if s.get("misses", 0) != 0]

                if isinstance(best_scores, list) and best_scores:
                    if miss_limit is not None:
                        best_scores = [s for s in best_scores if s.get("misses", 0) <= miss_limit]
                    page_size = 5
                    total_pages = (len(best_scores) + page_size - 1) // page_size

                context.user_data["best_scores"] = best_scores
                context.user_data["user_data"] = user_data
                context.user_data["total_pages"] = total_pages

                if "user_data" not in context.user_data:
                    context.user_data["user_data"] = {}

                context.user_data["user_data"]["live_pp"] = live_pp
                context.user_data["user_data"]["new_total"] = new_total

                page_size = 10
                total_pages = (len(best_scores) + page_size - 1) // page_size
                page = 0

                text = get_page_text_choke(user_data, best_scores, page)
                keyboard = get_pagination_keyboard_choke(page, total_pages, update.effective_user.id)

    
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )


                return
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при nochoke (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Непонятно... Попробуй еще раз через несколько секунд!`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )
def get_page_text_choke(user_data, best_scores, page=0, page_size=5):
    start = page * page_size
    end = start + page_size
    lines = []
    a, b = float(user_data["live_pp"]), float(user_data["new_total"])
    lines.append(f'<b>Total pp: {a:.2f} → {b:.2f}pp (+{(b-a):.2f})</b>')
    lines.append("")       
    for i, score in enumerate(best_scores[start:end], start=start):
        # score["weight_percent"] = 0.95 ** i

        title = html.escape(score.get("title", ""))
        version = html.escape(score.get("version", ""))
        mods = score.get("mods", [])
        mods_str = "NM" if not mods else "".join(mods)
        if score.get('lazer') == False:
            mods_str += 'CL'
        mods_str = html.escape(mods_str)        
        stars = score.get("stars", 0)
        pp_old = f"{score.get('pp_old',0):.2f}"
        pp_new = f"{score.get('pp_new',0):.2f}"
        misses = str(score.get("misses", 0))
        map_id = score.get("beatmap_id")

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"http://myangelfujiya.ru/index.html?id={map_id}"

        line1 = f'<b>#{score.get("index")}</b> <a href="{url}">{title} [{version}]</a> <b>+{mods_str}</b> [{stars:.2f}★]'
        line2 = f'<a href="{url_2}">🔗</a> <code>{pp_old}</code> → <b>{pp_new}pp</b> • <i>Removed {misses}❌</i>'

        lines.append(line1)
        lines.append(line2)
        lines.append("")

    username = html.escape(user_data["username"])
    stats = user_data["statistics"]
    pp_text = f"{stats.get('pp', 0):.2f}"
    global_rank_text = f"(#{stats.get('global_rank'):,})" if stats.get("global_rank") else "(#????)"
    country_rank_text = f"{user_data['country_code']}#{stats.get('country_rank'):,}" if stats.get("country_rank") else f"{user_data['country_code']}#??"
    rank_text = f"{username}: {pp_text}pp {global_rank_text} {country_rank_text}"
    country_flag = country_code_to_flag(user_data["country_code"])
    user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
    user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

    text = f"{user_link}\n\n" + "\n".join(lines)
    return text

def get_pagination_keyboard_choke(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_{user_id}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("След. страница ➡️", callback_data=f"page_{page+1}_{user_id}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None

async def page_callback_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 

    best_scores = context.user_data.get("best_scores", [])
    user_data = context.user_data.get("user_data")
    total_pages = context.user_data.get("total_pages", 1)

    _, page_str, owner_id_str = query.data.split("_")
    owner_id = int(owner_id_str)
    if query.from_user.id != owner_id:
        await query.answer("Это не ваша команда!", show_alert=True)
        return

    page = int(page_str)
    text = get_page_text_choke(user_data, best_scores, page)  # твоя функция генерации текста
    keyboard = get_pagination_keyboard_choke(page, total_pages, owner_id)

    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

async def show_scores_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    best_scores = context.user_data.get("best_scores", [])
    user_data = context.user_data.get("user_data")
    total_pages = context.user_data.get("total_pages", 1)

    user_id = update.effective_user.id
    page = 0
    text = get_page_text_choke(user_data, best_scores, page)
    keyboard = get_pagination_keyboard_choke(page, total_pages, user_id)

    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

# avg stats cmd
async def start_average_stats(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(average_stats(update, context, user_request))
async def average_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="average_stats",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/average_stats fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", 
        parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)
            

            if isinstance(best_scores, list) and best_scores:
                def format_value(val, is_time=False):
                    if is_time:
                        minutes = int(val // 60)
                        seconds = int(val % 60)
                        return f"{minutes}:{seconds:02d}"
                    if isinstance(val, float):
                        return f"{val:.2f}"
                    return str(val)

                accs, combos, misses, pps = [], [], [], []
                stars, ars, css, hps, ods, bpms, lengths = [], [], [], [], [], [], []

                # beatmap_requests = []
                # for score in best_scores:
                #     beatmap_requests.append({
                #         "beatmap_id": score.get("beatmap_id"),
                #         "mods": score.get("mods", []),  # список модов
                #         "ruleset_id": 0  # стандартный osu! ruleset
                #     })

                # attributes_list = await get_beatmap_attributes_batch(beatmap_requests, token=token, parallel_limit=5, delay_between_batches=0.1)

                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    accs.append(score.get("accuracy", 0.0) * 100)  # accuracy в %
                    combos.append(score.get("combo", 0))
                    misses.append(score.get("misses", 0))
                    pps.append(score.get("pp", 0.0))
                    # stars = (score.get("stars", 0.0))
                    ar = (score.get("AR", 0.0))
                    cs = (score.get("CS", 0.0))
                    hp = (score.get("HP", 0.0))
                    od = (score.get("OD", 0.0))
                    bpm = (score.get("bpm", 0.0))
                    length = (score.get("length", 0))
                    
                    mods_str = score.get("mods", "")
                    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)
                   
                    #neko API 
                    payload = {
                        "map_path": str(score.get('beatmap_id', "0")), 
                        
                        "n300": 0,
                        "n100": 0,
                        "n50": 0,
                        "misses": 0,                   
                        
                        "mods": str(mods_str), 
                        "combo": int(0),      
                        "accuracy": float(0.0),    
                        
                        "lazer": bool(True),          
                        "clock_rate": float(1.0),  

                        "custom_ar": float(ar),
                        "custom_cs": float(cs),
                        "custom_hp": float(hp),
                        "custom_od": float(od),
                    }

                    try:
                        pp_data = await localapi.get_map_stats_neko_api(payload)

                        # pp = pp_data.get("pp")
                        # choke = pp_data.get("no_choke_pp")
                        # max_pp = pp_data.get("perfect_pp")

                        map_stars = pp_data.get("star_rating")
                        # max_combo = pp_data.get("perfect_combo")
                        # expected_bpm = pp_data.get("expected_bpm")

                        # n300 = pp_data.get("n300")
                        # n100 = pp_data.get("n100") 
                        # n50 = pp_data.get("n50")
                        # expected_miss = pp_data.get("misses")

                        # aim_raw = pp_data.get("aim")
                        # acc_raw = pp_data.get("acc")
                        # speed_raw = pp_data.get("speed")                        
                        
                        if map_stars > 8.0: 
                            print(score['beatmap_id'])
                    except Exception as e:
                        print(f"neko API failed: {e}")

                    stars.append(map_stars)

                    bpm, ar, od, cs, hp = apply_mods_to_stats(
                        bpm, ar, od, cs, hp,
                        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                    )
                    length = int(round(float(length) / speed_multiplier))

                    ars.append(ar)
                    css.append(cs)
                    hps.append(hp)
                    ods.append(od)
                    bpms.append(bpm)
                    lengths.append(length)

                                    
                def calc_stats(values):
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    if not numeric_values:
                        return ("-", "-", "-")
                    return (min(numeric_values), mean(numeric_values), max(numeric_values))

                def format_time(seconds):
                    if isinstance(seconds, str):
                        return seconds
                    m, s = divmod(int(round(seconds)), 60)
                    h, m = divmod(m, 60)
                    if h > 0:
                        return f"{h}:{m:02d}:{s:02d}"
                    return f"{m}:{s:02d}"

                table_data = {
                    "Accuracy": calc_stats(accs),
                    "Combo": calc_stats(combos),
                    "Misses": calc_stats(misses),
                    "Stars": calc_stats(stars),
                    "PP": calc_stats(pps),
                    "AR": calc_stats(ars),
                    "CS": calc_stats(css),
                    "HP": calc_stats(hps),
                    "OD": calc_stats(ods),
                    "BPM": calc_stats(bpms),
                    "Length": calc_stats(lengths),
                }

                formatted_table_data = {}
                for key, values in table_data.items():
                    formatted_values = []
                    for v in values:
                        if isinstance(v, str):
                            formatted_values.append(v)
                        elif key == "Length":
                            formatted_values.append(format_time(v))
                        elif isinstance(v, float):
                            formatted_values.append(f"{v:.2f}")
                        else:
                            formatted_values.append(str(v))
                    formatted_table_data[key] = formatted_values

                headers = ["", "Minimum", "Average", "Maximum"]
                rows = [[key, *values] for key, values in formatted_table_data.items()]

                col_widths = [
                    max(len(str(headers[i])), max(len(str(row[i])) for row in rows))
                    for i in range(len(headers))
                ]

                def fmt_row(row):
                    return " | ".join(
                        str(row[i]).ljust(col_widths[i]) if i == 0 else str(row[i]).center(col_widths[i])
                        for i in range(len(row))
                    )

                header_line = fmt_row(headers)
                sep_line = "-+-".join("-" * w for w in col_widths)
                table_lines = [header_line, sep_line] + [fmt_row(row) for row in rows]

                table_str = "\n".join(table_lines)

                username = user_data["username"]
                stats = user_data["statistics"]

                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )

                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

                text = f"{user_link}\n\n<pre>{table_str}</pre>"


                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"            
                )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при average_stats (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
async def post_with_timeout(session: aiohttp.ClientSession, url: str, headers: dict, json_body: dict, timeout: int = 10):
    async with session.post(url, headers=headers, json=json_body, timeout=timeout) as response:
        response.raise_for_status()
        return await response.json()
async def fetch_attributes_single(beatmap_id: int, mods: List[str], ruleset_id: int, token: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> Dict | None:
    url = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}/attributes"
    body = {"mods": mods, "ruleset_id": ruleset_id}
    async with semaphore:  
        data = await try_request(post_with_timeout, retries=3, session=session, url=url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }, json_body=body)
        return data.get("attributes")
async def get_beatmap_attributes_batch(beatmap_requests: List[Dict], token: str = None, parallel_limit: int = 5, delay_between_batches: float = 0.2) -> List[Dict | None]:
    """
    beatmap_requests = [
        {"beatmap_id": 123, "mods": ["HD"], "ruleset_id": 0},
        {"beatmap_id": 456, "mods": ["HR"], "ruleset_id": 0},
        ...
    ]
    """
    if token is None:
        token = await try_request(get_osu_token, retries=3)

    semaphore = asyncio.Semaphore(parallel_limit)
    results = []

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(beatmap_requests), parallel_limit):
            batch = beatmap_requests[i:i+parallel_limit]
            tasks = [
                fetch_attributes_single(req["beatmap_id"], req["mods"], req["ruleset_id"], token, session, semaphore)
                for req in batch
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            await asyncio.sleep(delay_between_batches)

    return results

async def get_beatmapset_md5(replay_path: str) -> str:
    replay = Replay.from_path(replay_path)
    return replay.beatmap_hash
async def get_beatmapset_id_from_md5(md5_hash: str, token: str) -> int:
    if token is None:
        token = await get_osu_token()
    url = f"https://osu.ppy.sh/api/v2/beatmaps/lookup?checksum={md5_hash}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["beatmapset_id"]
async def get_beatmapset_id(replay_path: str, token: str) -> int:
    md5_hash = await get_beatmapset_md5(replay_path)
    return await get_beatmapset_id_from_md5(md5_hash, token)
async def download_osz_async(mapset_id: int, osu_session: str, save_dir: str,
                             connect_timeout: int = 5, read_timeout: int = 60, chunk_size: int = 8192):
    extract_dir = os.path.join(save_dir, str(mapset_id))
    if os.path.exists(extract_dir):
        print(f"using cache {extract_dir}")
        return extract_dir

    os.makedirs(save_dir, exist_ok=True)

    url = f"https://osu.ppy.sh/beatmapsets/{mapset_id}/download"
    cookies = {"osu_session": osu_session}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": f"https://osu.ppy.sh/beatmapsets/{mapset_id}"
    }

    osz_path = os.path.join(save_dir, f"{mapset_id}.osz")

    timeout = aiohttp.ClientTimeout(sock_connect=connect_timeout, sock_read=read_timeout)

    async with aiohttp.ClientSession(timeout=timeout, cookies=cookies, headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise ValueError(f"{mapset_id}{resp.status}")

            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                raise ValueError("HTML, not OSZ")

            async with aiofiles.open(osz_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    if chunk:
                        await f.write(chunk)

    print(f"Скачано: {osz_path}")

    os.makedirs(extract_dir, exist_ok=True)

    def _extract():
        with zipfile.ZipFile(osz_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        os.remove(osz_path)

    await asyncio.to_thread(_extract)

    return extract_dir
def download_osr(score_id: int, osu_session: str, save_dir: str) -> str:
    url = f"https://osu.ppy.sh/scores/{score_id}/download"
    cookies = {"osu_session": osu_session}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://osu.ppy.sh/scores/{score_id}"
    }

    replay_path = os.path.join(save_dir, f"{score_id}.osr")

    with requests.get(url, cookies=cookies, headers=headers, stream=True) as r:
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise ValueError("Получен HTML вместо OSR. Проверь куки и score_id.")

        with open(replay_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

    print(f"Скачан реплей: {replay_path}")
    return replay_path  

def compress_video_if_needed(input_path: str, max_size_mb: int = 45) -> str:   
    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:        
        return input_path

    base, ext = os.path.splitext(input_path)
    compressed_path = f"{base}_compressed{ext}"

    ffmpeg_command = [
        "ffmpeg",
        "-y",  
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "28",      
        "-preset", "fast",  
        "-acodec", "aac",
        compressed_path
    ]

    subprocess.run(ffmpeg_command, check=True)

    return compressed_path
def cleanup_files(*file_paths: str):
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {file_path}")
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")

#new features zone



#new card cmd
async def start_beatmap_card(update, context, user_request=True):
    if user_request: await log_all_update(update)
    asyncio.create_task(beatmap_card(update, context, user_request))
async def beatmap_card(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):    
    try:
        message_text = update.message.text.strip()
        match = OSU_MAP_REGEX.search(message_text)
        message = update.message
        if user_request:
            if not match:        
                msg = await update.message.reply_text(
                    "❌ Нужна ссылка на карту"
                )
                asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
                asyncio.create_task(delete_user_message(update, context, delay=4))
                return
        
        if match is None: return
        beatmap_id = match.group(1) if match.group(1) else match.group(2)
    
        if user_request: warn_text = f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        else: warn_text = None
        can_run = await check_user_cooldown(
            command_name="render_score",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=warn_text
        )
        if not can_run:
            return
    
    except Exception as e:
        print(e)
        return
    
    

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                if update.message:
                    temp_message = await update.message.reply_text(
                        "`Загрузка...`",
                        parse_mode="Markdown"
                    )
                break
            except Exception as e: print(e)
    
    for _ in range(max_attempts):
        try:             
            maps_ids = []
            maps_ids.append(beatmap_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(beatmap_id, token)

            def format_length(seconds: int) -> str:
                h, m = divmod(seconds, 3600)
                m, s = divmod(m, 60)
                if h > 0:
                    return f"{h}:{m:02}:{s:02}"
                return f"{m}:{s:02}"

            bpm_map = map_data['bpm']
            mode = map_data['mode_int']
            if mode != 0: return
            length = format_length(map_data['total_length'])
            version = map_data['version']
            status = map_data['status']
            circles, sliders = map_data['count_circles'], map_data['count_sliders']
            updated = map_data['last_updated']
            plays = f"{map_data['playcount']:,}"
            psc = map_data['passcount']
            max_combo_map = f" (x{map_data['max_combo']:,})"
            mapper = map_data['owners'][0]['username']
            artist = map_data['beatmapset']['artist']
            creator = map_data['beatmapset']['creator']
            title = map_data['beatmapset']['title'] +" - " + artist + ' [' + version +']'           
            favs =  f"{map_data['beatmapset']['favourite_count']:,}"

            bg_url = map_data['beatmapset']['covers']['cover']
            
            extra_img = None
            now = datetime.now()
            bg_file = None
            for f in os.listdir(COVERS_DIR):
                if f.startswith(f"{beatmap_id}_") and f.endswith(".png"):
                    path = os.path.join(COVERS_DIR, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    if now - mtime < timedelta(hours=1):  # файл свежий, используем
                        bg_file = path
                        break
                
            if bg_file:
                extra_img = Image.open(bg_file).convert("RGBA")
                bg_path = bg_file
                print("using cached bg")
            else:
                bg_path = os.path.join(COVERS_DIR, "default.png")
                extra_img = None
                MAX_ATTEMPTS = 2
                for attempt_bg in range(1, MAX_ATTEMPTS + 1):
                    try:
                        timeout = aiohttp.ClientTimeout(total=3)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(bg_url) as resp:
                                if resp.status == 200:
                                    def add_rounded_corners(imge: Image.Image, radius: int) -> Image.Image:
                                        # создаем маску в два раза больше для сглаживания
                                        big_size = (imge.size[0]*2, imge.size[1]*2)
                                        mask = Image.new("L", big_size, 0)
                                        draw_mask = ImageDraw.Draw(mask)
                                        draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                        
                                        # сжимаем маску обратно для сглаживания
                                        mask = mask.resize(imge.size, Image.LANCZOS)
                                        
                                        # применяем альфу
                                        imge.putalpha(mask)
                                        return imge
                                    extra_img_data = await resp.read()
                                    extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                                    extra_img.thumbnail((512, 512))
                                    extra_img = add_rounded_corners(extra_img, radius=12)
                                    bg_filename = f"{beatmap_id}_{now.hour}{now.minute}.png"
                                    bg_path = os.path.join(COVERS_DIR, bg_filename)
                                    extra_img.save(bg_path, format="PNG")
                                    break
                    except Exception as e:
                        print(f"Ошибка при скачивании аватарки: {e}")
            path, values = await beatmap(beatmap_id)
           
            #neko API 
            payload = {
                "map_path": str(beatmap_id), 
                
                "n300": 0,
                "n100": 0,
                "n50": 0,
                "misses": 0,                   
                
                "mods": str(""), 
                "combo": int(0),      
                "accuracy": float(100),    
                
                "lazer": bool(True),          
                "clock_rate": float(1.0),  

                "custom_ar": values.get("ar"),
                "custom_cs": values.get("cs"),
                "custom_hp": values.get("hp"),
                "custom_od": values.get("od"),
            }

            try:
                pp_data = await localapi.get_map_stats_neko_api(payload)

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

                aim_raw = pp_data.get("aim")
                acc_raw = pp_data.get("acc")
                speed_raw = pp_data.get("speed")
            
            except Exception as e:
                print(f"neko API failed: {e}")
            
            mods_list = ["NM", "EZ", "HR", "DT", "HR+DT"]

            ar_values = []
            od_values = []
            cs_values = []
            hp_values = []

            for mods_str in mods_list:
                speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

                bpm, ar, od, cs, hp = apply_mods_to_stats(
                    expected_bpm, values.get("ar"), values.get("od"), values.get("cs"), values.get("cs"),
                    speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                )

                ar_values.append(round(ar, 2))
                od_values.append(round(od, 2))
                cs_values.append(round(cs, 2))
                hp_values.append(round(hp, 2))

            fill_colors = [(255,255,255), (98, 240, 124), (240, 223, 98), (240,128,98), (200,200,200)]
          

            values = {
                "speed": speed_raw,
                "acc": acc_raw,
                "aim": aim_raw
            }

            max_val = max(values.values())

            normalized = {k: v / max_val for k, v in values.items()}

            speed_data = normalized["speed"]
            acc_data   = normalized["acc"]
            aim_data   = normalized["aim"]

            width = 1400
            height = 800
            padding = 480

            img = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/bg.png").convert("RGBA")
            draw = ImageDraw.Draw(img)

            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/mapcard.png").convert("RGBA")
            img.paste(asset, (0, 0), mask=asset.split()[3])


            font_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 38)
            font_black_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 40)
            font_bold_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 22)
            font_noto = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/NotoEmoji.ttf", 46)
            font_regular_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 26)
            font_bold_med_3 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 28)
            font_bold_med_4 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 34)
            font_black_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 28)
            font_thin_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Thin.ttf", 28)
            font_light_italic_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 30)
            font_black_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 44)
            font_black_big_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 30)
            font = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 32)


            offset_x_w = 380
            offset_y_w = 145
            x1, x2 = padding + offset_x_w, width - padding + offset_x_w
            unit1 = (x2 - x1) / (4 + 4*2 + 2*4)  
            # 1-5: 4 шагов по 1
            # 5-9: 4 шагов по 2 (2к1)
            # 9-11: 2 шагов по 4 (4к1)

            def value_to_x_custom(val):
                if val <= 5:
                    return x1 + (val - 1) * unit1
                elif val <= 9:
                    return x1 + 4*unit1 + (val - 5) * 2 * unit1
                else:  # 9-11
                    return x1 + 4*unit1 + 8*unit1 + (val - 9) * 4 * unit1

            # Генерируем деления
            scale_1_5 = [1, 2, 3, 4, 5]
            scale_5_9 = [5 + i*0.5 for i in range(1, 9)]  # 5.5,6,6.5 ...9
            scale_9_11 = [9 + i*0.25 for i in range(1, 9)]  # 9.25,9.5,...11
            all_scale = scale_1_5 + scale_5_9 + scale_9_11

            def draw_textbox_center(draw, x_center, y_top, text, font, fill_text=(255,255,255), fill_box=None, padding=2):
                bbox = draw.textbbox((0,0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = x_center - text_width/2
                y = y_top
                if fill_box:
                    draw.rectangle([x-padding, y-padding, x+text_width+padding, y+text_height+padding], fill=fill_box)
                draw.text((x, y), text, fill=fill_text, font=font)

            # y_positions = [120, 305, 405]
            # for y in y_positions:
            #     draw.line((x1 -10, y, x2 + 10, y), fill=(150,150,150), width=1)
            # Вертикальные линии
            y_grid_top = 10 + offset_y_w
            y_grid_bottom = 150 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                # выделяем целые числа жирнее
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    if val not in (1, 2, 4, 3):
                        draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)

            y_grid_top = 195 + offset_y_w
            y_grid_bottom = 420 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                # выделяем целые числа жирнее
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    if val not in (1, 2, 4, 3):
                        draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)

            y_grid_top = 465 + offset_y_w
            y_grid_bottom = 600 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                # выделяем целые числа жирнее
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    # if val not in (1, 2, 4, 3):
                        # draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)




            # Рисуем полосы без цикла, как у тебя было
            bar_offset_y = 20 + offset_y_w
            val = cs_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = cs_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = cs_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = cs_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 205 + offset_y_w
            val = ar_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = ar_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = ar_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = ar_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 305 + offset_y_w
            val = od_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = od_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = od_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = od_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 485 + offset_y_w
            val = hp_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = hp_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = hp_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = hp_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)


            text_x, text_y, text_b = 797, 172, 43
            draw_textbox_center(draw, text_x, text_y, "| CS", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{cs_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  356, 43
            draw_textbox_center(draw, text_x, text_y, "| AR", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{ar_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  458, 43
            draw_textbox_center(draw, text_x, text_y, "| OD", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{od_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  637, 43
            draw_textbox_center(draw, text_x, text_y, "| HP", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{hp_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_x, text_y, text_b = 776, 295, 43
            draw_textbox_center(draw, text_x, text_y, "NM", font_bold_med)
            text_x, text_y, text_b = 820, 295, 43
            draw_textbox_center(draw, text_x, text_y, "HR", font_bold_med, fill_text=fill_colors[2])

            text_x, text_y, text_b = 769, 577, 43
            draw_textbox_center(draw, text_x, text_y, "DT", font_bold_med, fill_text=fill_colors[3])
            text_x, text_y, text_b = 820, 577, 43
            draw_textbox_center(draw, text_x, text_y, "DTHR", font_bold_med, fill_text=fill_colors[4])




            bars = [
                {"left": 100, "value": aim_data},
                {"left": 310, "value": acc_data},
                {"left": 520, "value": speed_data}
            ]

            bar_width = 160
            bar_y0 = 578
            bar_height = 14
            bar_y1 = bar_y0 + bar_height
            radius = bar_height  

            for bar in bars:
                bar_left = bar["left"]
                bar_right = bar_left + bar_width
                
                draw.line(
                    (bar_left, bar_y0 + bar_height // 2, bar_right, bar_y0 + bar_height // 2),
                    fill="white", width=2
                )

                fill_len = int(bar_width * bar["value"])
                if fill_len > 0:
                    draw.rounded_rectangle(
                        [bar_left, bar_y0, bar_left + fill_len, bar_y1],
                        radius=radius,
                        fill="white"
                    )


            text_x, text_y, text_b = 180, 525, 75
            draw_textbox_center(draw, text_x, text_y, "| AIM", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{aim_raw:.0f}"), font_black_small, fill_text=fill_colors[0])

            text_x = 390
            draw_textbox_center(draw, text_x, text_y, "| ACC", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{acc_raw:.0f}"), font_black_small, fill_text=fill_colors[0])

            text_x = 604
            draw_textbox_center(draw, text_x, text_y, "| SPEED", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{speed_raw:.0f}"), font_black_small, fill_text=fill_colors[0])


            spacing_y = 55
            base_x, base_y = 470, 136

            def draw_emoji_text(draw, x, y, emoji, text, emoji_font, text_font, text_fill):
                bbox = emoji_font.getbbox(emoji)
                emoji_width = bbox[2] - bbox[0]

                draw.text((x, y), emoji, font=emoji_font, fill="white", anchor="lm")  # anchor чтобы центрировать по Y
                draw.text((x + emoji_width + 8, y), text, font=text_font, fill=text_fill, anchor="lm")

            draw_emoji_text(draw, base_x, base_y + spacing_y, "▶️", str(plays), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*2, "💖", str(favs), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*3, "⏰", (str(length) + max_combo_map), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*4, "🥁", str(bpm_map), font_noto, font_regular_nano, fill_colors[0])

            draw.line((480, 395, 690, 395), fill=(200,200,200), width=2)

            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/circle.png").convert("RGBA")

            base_width = 35
            block_right = 680

            w_percent = base_width / float(asset.size[0])
            new_height = int(float(asset.size[1]) * w_percent)

            asset = asset.resize((base_width, new_height), Image.LANCZOS)
            img.paste(asset, (497, 410), asset)

            text = str(circles)
            text_bbox = draw.textbbox((0,0), text, font=font_bold_med_3)
            text_width = text_bbox[2] - text_bbox[0]

            draw.text((block_right - text_width, 410), text, font=font_bold_med_3, fill="white")


            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/slider.png").convert("RGBA")

            base_width = 50
            w_percent = base_width / float(asset.size[0])
            new_height = int(float(asset.size[1]) * w_percent)

            asset = asset.resize((base_width, new_height), Image.LANCZOS)
            img.paste(asset, (490, 460), asset)

            text = str(sliders)
            text_bbox = draw.textbbox((0,0), text, font=font_bold_med_3)
            text_width = text_bbox[2] - text_bbox[0]

            draw.text((block_right - text_width, 460), text, font=font_bold_med_3, fill="white")

            
            line_y = 270
            draw.line((100, line_y, 412, line_y), fill=(150,150,150), width=2)

            draw.text((100, 280), f"last update: {format_osu_date(updated, False)}", font=font_regular_nano, fill=(150,150,150))
            # draw_emoji_text(draw, 100, 340, "👤", str(" "), font_noto, font_regular_nano, fill_colors[0])
            draw.text((100, 320), str(mapper), font=font_bold_med_4, fill="white")
            line_y = 370
            draw.line((100, line_y, 412, line_y), fill=(200,200,200), width=2)


            draw_emoji_text(draw, 100, 405, "⭐️", str(f"{stars:.2f}"), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, 100, 465, "📊", status.capitalize(), font_noto, font_regular_nano, fill_colors[0])

            draw_emoji_text(draw, 250, 405, "💯", str(f"{max_pp:.1f}pp"), font_noto, font_regular_nano, fill_colors[0])
            

            # Подвал
            bot_first, bot_second = "Fujiyaosu", "Bot"
            today = date.today().isoformat()
            draw.text((128, 729), bot_first, font=font_black_small_2, fill="white")
            bbox = draw.textbbox((0, 0), bot_first, font=font_black_small_2)
            text_width = bbox[2] - bbox[0]
            draw.text((128+text_width, 729), bot_second, font=font_thin_small, fill="white")

            draw.text((428, 729), today, font=font_light_italic_big, fill="white")

            mode = "Standard"
            asset = Image.open(f"{BOT_DIR}/cards/assets/gamemodes/{mode}.png").convert("RGBA")
            asset = asset.resize((70,70))
            img.paste(asset, (1315, 15), asset)

            asset = Image.open(f"{BOT_DIR}/cards/assets/branding/icon.png").convert("RGBA")
            asset = asset.resize((110,110))
            img.paste(asset, (0, 690), asset)


            block_left = 32
            block_right = 1300 
            max_width = block_right - block_left



            # --- Подбор заголовка ---
            words = title.split()

            def wrap_text(words, font, max_width, draw):
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    line_width = draw.textlength(test_line, font=font)
                    if line_width <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                return lines

            # Сначала считаем с большим шрифтом
            lines = wrap_text(words, font_black_big, max_width, draw)

            if len(lines) == 1:
                title_y = 23
                font_text = font_black_big
            else:
                # если получилось больше одной строки — пересчёт с меньшим шрифтом
                lines = wrap_text(words, font_black_big_2, max_width, draw)
                lines = lines[:2]  # максимум две строки
                title_y = 15
                font_text = font_black_big_2

            title_multiline = "\n".join(lines)
            draw.text((block_left, title_y), title_multiline, font=font_text, fill=(255, 255, 255), spacing=14)

            bg = Image.open(bg_path).convert("RGBA").resize((380, 106))
            img.paste(bg, (67, 148), bg)

            img_path = f'{BOT_DIR}/cache/{beatmap_id}.png'
            img.convert("RGB").save(img_path) 

            with open(img_path, "rb") as f:
                try:
                    await message.reply_photo(
                        InputFile(f),
                    )
                except:
                    await message.reply_photo(
                        InputFile(f),
                    )
                if user_request:
                    try:
                        
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                    except:
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                try:
                    os.remove(img_path)
                except: return 
                return
  
        except Exception as e: print(e)   



#music cmd
async def start_beatmap_audio(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(beatmap_audio(update, context, user_request))
async def beatmap_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):
    url = update.message.text.strip()
    match = re.search(r"beatmapsets/(\d+)", url)

    if user_request:
        if not match:        
            msg = await update.message.reply_text(
                "❌ Нужна ссылка на карту"
            )
            asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
            asyncio.create_task(delete_user_message(update, context, delay=4))
            return
    
    try:
        if match is None: return
        beatmap_id = match.group(1)
    except Exception as e:
        print(e)
        return

    if user_request: warn_text = f"⏳ Подождите {COOLDOWN_MP3_COMMAND} секунд"
    else: warn_text = None
    can_run = await check_user_cooldown(
        command_name="render_score",
        user_id=str(update.effective_user.id),
        cooldown_seconds=COOLDOWN_MP3_COMMAND,           
        update=update,
        context=context,
        warn_text=warn_text
    )
    if not can_run:
        return

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                status_msg = await update.message.reply_text("Загрузка...")
                break
            except Exception as e: print(e)
    
    for _ in range(max_attempts):
        try: 
            await download_osz_async(beatmap_id, OSU_SESSION, OSZ_DIR)

            break
        except Exception as e: print(e)   

    path = os.path.join(OSZ_DIR, beatmap_id)

    title, artist, path, bg_path = await beatmap_artists_and_audio_path(path)

    path = os.path.join(OSZ_DIR, beatmap_id, path)
    bg_path = os.path.join(OSZ_DIR, beatmap_id, bg_path)

    await send_audio(update, context, path, title, artist, bg_path)
    if user_request:
        asyncio.create_task(delete_message_after_delay(context, status_msg.chat_id, status_msg.message_id, 1)) 
async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, audio_file_path, title=None, artist=None, bg=None):
    path = Path(audio_file_path)
    if not path.is_file():
        print("Файл не найден:", audio_file_path)
        return
    if os.path.getsize(audio_file_path) == 0:
        print("Файл пустой:", audio_file_path)
        return

    temp_file = None
    try:
        if path.suffix.lower() == ".ogg":
            # создаём временный файл с расширением .mp3
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()  # закрываем, чтобы pydub смог писать
            audio = AudioSegment.from_file(audio_file_path, format="ogg")
            audio.export(temp_file.name, format="mp3")
            send_path = Path(temp_file.name)
        else:
            send_path = path

        username = escape_markdown(update.effective_user.username, version=2)
        link = "https://t.me/fujiyaosubot"
        caption = f"@{username} 💃 [ᴅᴀʀᴋɴᴇss]({link})"

        with open(send_path, "rb") as f:
            kwargs = {
                "audio": InputFile(f, filename=send_path.name),
                "caption": caption,
                "title": title or "",
                "parse_mode": "MarkdownV2",
            }
            if artist:
                kwargs["performer"] = artist

            await update.message.reply_audio(**kwargs)

    except Exception as e:
        print("Ошибка при отправке аудио:", e)
    finally:
        # удаляем временный файл, если он был
        if temp_file:
            try:
                os.remove(temp_file.name)
            except OSError:
                pass
async def beatmap_artists_and_audio_path(folder_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Ищет первый .osu в папке и возвращает:
    (строка "Title - Artist" (Unicode если есть), имя аудиофайла)
    """
    osu_files = [f for f in os.listdir(folder_path) if f.endswith(".osu")]
    if not osu_files:
        print(f"⚠ В папке {folder_path} нет .osu файлов")
        return None, None

    path_to_map = os.path.join(folder_path, osu_files[0])

    title = None
    artist = None
    title_unicode = None
    artist_unicode = None
    audio_filename = None
    bg_path = None

    try:
        with open(path_to_map, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TitleUnicode:"):
                    title_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("ArtistUnicode:"):
                    artist_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("Artist:"):
                    artist = line.split(":", 1)[1].strip()
                elif line.startswith("AudioFilename:"):
                    audio_filename = line.split(":", 1)[1].strip()
                elif '"' in line and any(ext in line.lower() for ext in [".jpg", ".jpeg", ".png"]):
                    m = re.search(r'"([^"]+\.(?:jpg|jpeg|png))"', line, re.IGNORECASE)
                    if m:
                        bg_path = m.group(1)
                if (title_unicode or title) and (artist_unicode or artist) and audio_filename and bg_path:
                    break
    except Exception as e:
        print(f"⚠ Ошибка при парсинге {path_to_map}: {e}")
        return None, None, None, None

    final_title = title_unicode if title_unicode else title
    final_artist = artist_unicode if artist_unicode else artist

    return final_title, final_artist, audio_filename, bg_path


def search_beatmaps(db_path, mods=None, filters=None, limit=10, offset=0, order_by_total=True, lazer=True):
                """
                db_path: путь к beatmaps.db
                mods: список модов, например ["DTHD", "HR"]
                filters: словарь с ключами 'aim', 'speed', 'acc', значениями кортежа (operator, value) или (min, max)
                        Пример: {"aim": (100, 200), "speed": (90, 140), "acc": (">", 90)}
                limit: количество результатов
                offset: смещение
                order_by_total: сортировать по сумме aim+speed+acc
                """

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()

                where_clauses = []
                params = []

                if mods:
                    placeholders = ",".join("?" for _ in mods)
                    where_clauses.append(f"mod IN ({placeholders})")
                    params.extend(mods)

                if filters:
                    for stat, val in filters.items():
                        if isinstance(val, tuple) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
                            
                            where_clauses.append(f"{stat} BETWEEN ? AND ?")
                            params.extend(val)
                        elif isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], str):
                            
                            op, v = val
                            where_clauses.append(f"{stat} {op} ?")
                            params.append(v)

                where_clauses.append("mode = ?")
                params.append("lazer" if lazer else "stable")

                where_sql = " AND ".join(where_clauses)
            
                sql = f"""
                    SELECT map_id, mode, mod, aim, speed, acc, (aim + speed + acc) AS total
                    FROM beatmaps
                    {f'WHERE {where_sql}' if where_sql else ''}
                    {'ORDER BY total DESC' if order_by_total else ''}
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])

                cur.execute(sql, params)
                results = cur.fetchall()
                conn.close()
                return results
async def start_farm(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(farm(update, context, user_request))
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="farm",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_FARM_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_FARM_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    if not context.args:
        if saved_name:
            username = saved_name
        else:       
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Для использования этой команды должно быть сохранено имя /name`" ,
                    parse_mode="Markdown"
                )
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:  
            try: 
                if os.path.exists(USERS_SKILLS_FILE):
                    with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
                        users_skills = json.load(f)
                else:    
                    users_skills = {}
                
                if username in users_skills:
                    skills = users_skills[username].get("values", {})
                else:
                    raise ValueError(f"Пользователь {username} не найден в JSON")        
            except Exception as e:
                print(e)
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет данных о карточке пользователя... Может быть стоит создать новую командой /card, а после этого вернуться сюда?`",
                    parse_mode="Markdown"
                )
                return

            context.user_data["farm_user_id"] = update.effective_user.id
            context.user_data["farm_choices"] = {}
            context.user_data["farm_step"] = 0
            context.user_data["farm_topic_id"] = getattr(update.effective_message, "message_thread_id", None)

           
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"Версия:",
                    parse_mode="Markdown",
                    reply_markup=get_farm_step_keyboard(0)
            )

            return
        except Exception as e:
            print(f"Ошибка при farm (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
def create_pagination_keyboard(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"farm_page:{user_id}:{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"farm_page:{user_id}:{page+1}"))
    return InlineKeyboardMarkup([buttons])


async def farm_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action, user_id, page = data
    user_id = int(user_id)
    page = int(page)

    if query.from_user.id != user_id:
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    pages = context.user_data.get("farm_pages", [])
    if not pages:
        await query.edit_message_text("❌ Ошибка: данные не найдены")
        return

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
    else:
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    lines = []
    choices = context.user_data.get("farm_choices", {})
    skill_level = choices.get("skill", "1")
    percent = (float(choices.get("tol", 1.2)) - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[page]:
        map_id = beatmap[0]
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        def cmp_symbol(val, base):
            if val > base + 15:
                return "🔼"
            elif val < base - 15:
                return "🔽"
            else:
                return "🔅"

        symbols = "".join([            
            cmp_symbol(acc, acc_base),
            cmp_symbol(aim, aim_base),
            cmp_symbol(speed, speed_base),
        ])

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"http://myangelfujiya.ru/index.html?id={map_id}"

        line = f"{total_str}pts {symbols} [http://osu.p...]({url}) | [🔗]({url_2})   +{mods}"
        lines.append(line)

    text = "\n".join(lines)

    keyboard = create_pagination_keyboard(page, len(pages), user_id)  # <-- тоже page

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def get_farm_step_keyboard(step):
    if step == 1:
        buttons = [
            [
                InlineKeyboardButton("30%", callback_data="farm_skill:1"),
                InlineKeyboardButton("40%", callback_data="farm_skill:2"),
                InlineKeyboardButton("50%", callback_data="farm_skill:3"),
                InlineKeyboardButton("60%", callback_data="farm_skill:4"),
                InlineKeyboardButton("70%", callback_data="farm_skill:5"),
            ],
            [
                InlineKeyboardButton("80%", callback_data="farm_skill:6"),
                InlineKeyboardButton("90%", callback_data="farm_skill:7"),
                InlineKeyboardButton("100%", callback_data="farm_skill:8"),
                InlineKeyboardButton("110%", callback_data="farm_skill:9"),
                InlineKeyboardButton("120%", callback_data="farm_skill:10"),
            ]            
        ]
    elif step == 3:
        buttons = [
            [
                InlineKeyboardButton("NM", callback_data="farm_mod:NM"),
                InlineKeyboardButton("HD", callback_data="farm_mod:HD"),
                InlineKeyboardButton("HR", callback_data="farm_mod:HR"),                
                InlineKeyboardButton("DT", callback_data="farm_mod:DT"),
                
            ],
            [   
                InlineKeyboardButton("HDHR", callback_data="farm_mod:HDHR"),                
                InlineKeyboardButton("HDDT", callback_data="farm_mod:DTHD"),
                InlineKeyboardButton("DTHR", callback_data="farm_mod:DTHR"),
                InlineKeyboardButton("HDDTHR", callback_data="farm_mod:DTHDHR")
            ]
        ]
    elif step == 0:
        buttons = [
            [
                InlineKeyboardButton("Клиент Stable", callback_data="farm_lazer:False"),            
                InlineKeyboardButton("Клиент Lazer", callback_data="farm_lazer:True"),
            ],
            
        ]
    elif step == 2:
        buttons = [
            [
                InlineKeyboardButton("±10%", callback_data="farm_tol:1.1"),
                InlineKeyboardButton("±20%", callback_data="farm_tol:1.2"),
                InlineKeyboardButton("±30%", callback_data="farm_tol:1.3"),
                InlineKeyboardButton("±40%", callback_data="farm_tol:1.4"),
                InlineKeyboardButton("±50%", callback_data="farm_tol:1.5"),
            ],
            [
                InlineKeyboardButton("±60%", callback_data="farm_tol:1.6"),
                InlineKeyboardButton("±70%", callback_data="farm_tol:1.7"),
                InlineKeyboardButton("±80%", callback_data="farm_tol:1.8"),
                InlineKeyboardButton("±90%", callback_data="farm_tol:1.9"),
                InlineKeyboardButton("±100%", callback_data="farm_tol:2.0"),
            ]
        ]
    else:
        buttons = []
    return InlineKeyboardMarkup(buttons)

async def farm_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != context.user_data.get("farm_user_id"):
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    data = query.data.split(":")  # farm_skill:medium
    param_type, value = data

    if param_type == "farm_skill":
        context.user_data["farm_choices"]["skill"] = value
    elif param_type == "farm_mod":
        context.user_data["farm_choices"]["mod"] = value
    elif param_type == "farm_lazer":
        context.user_data["farm_choices"]["lazer"] = value == "True"
    elif param_type == "farm_tol":
        context.user_data["farm_choices"]["tol"] = value

    context.user_data["farm_step"] += 1
    step = context.user_data["farm_step"]

    if step > 3:
        await query.edit_message_text(f"⏳ @{query.from_user.username}...")
        await generate_farm_results(update, context)
    else:
        if step == 0: text="Клиент?"
        elif step == 1:text="Интенсивность фарма? (80-90% около топскора)"
        elif step == 2:text="Разброс, меньше - точнее уровень прошлого меню, а больше - больше карт за счет увеличения диапазона поиска"
        else:text="Моды, с которыми будет карта"
        await query.edit_message_text(
            text,
            reply_markup=get_farm_step_keyboard(step)
        )
async def generate_farm_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("farm_user_id")
    choices = context.user_data.get("farm_choices", {})
    topic_id = context.user_data.get("farm_topic_id", None)

    if not choices:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Ошибка: параметры поиска не выбраны"
        )
        return

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
        aim = skills.get("aim_total", 0)
        speed = skills.get("speed_total", 0)
        acc = skills.get("acc_total", 0)
        print(f"    Навыки пользователя {saved_name}: aim={aim}, speed={speed}, acc={acc}")
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Навыки пользователя не найдены. Создайте карточку через /card."
        )
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")


    skill_level = choices.get("skill", "low")
    mod = choices.get("mod", "NM")
    lazer = choices.get("lazer", "True")
    tol = float(choices.get("tol", 1.2))

    if skill_level == "1":
        base_start, base_end = 0.35, 0.45
    elif skill_level == "2":
        base_start, base_end = 0.45, 0.55
    elif skill_level == "3":
        base_start, base_end = 0.55, 0.65
    elif skill_level == "4":
        base_start, base_end = 0.65, 0.75
    elif skill_level == "5":
        base_start, base_end = 0.75, 0.85
    elif skill_level == "6":
        base_start, base_end = 0.85, 0.95
    elif skill_level == "7":
        base_start, base_end = 0.95, 1.05
    elif skill_level == "8":
        base_start, base_end = 1.05, 1.15
    elif skill_level == "9":
        base_start, base_end = 1.15, 1.25
    else:  # high
        base_start, base_end = 1.25, 1.35

    static_mult = 1.0
    start_mult = base_start / (tol*static_mult)
    end_mult = base_end * (tol*static_mult)

    #if skill_level == "floor":
    #    base_start, base_end = 0.4, 0.6
    #elif skill_level == "low":
    #    base_start, base_end = 0.6, 0.8
    #elif skill_level == "medium":
    #    base_start, base_end = 0.8, 1.0
    #else:  # high
    #    base_start, base_end = 1.0, 1.3

    #start_mult = base_start / tol 
    #end_mult = base_end * tol      

    filters = {
        "aim": (aim * start_mult, aim * end_mult),
        "speed": (speed * start_mult, speed * end_mult),
        "acc": (acc * start_mult, acc * end_mult)
    }

    mods = [mod]
    limit = 800
    offset = 0   

    try:
        results = search_beatmaps(
            db_path=f"{BOT_DIR}/beatmaps.db",
            mods=mods,
            filters=filters,
            limit=limit,
            offset=offset,
            lazer=lazer
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text=f"❌ Ошибка при поиске карт: {e}"
        )
        return

    if not results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="🚮 Ничего не найдено, попробуй увеличить разброс или другой уровень скилов."
        )
        return

    PAGE_SIZE = 8
    pages = [results[i:i+PAGE_SIZE] for i in range(0, len(results), PAGE_SIZE)]
    context.user_data["farm_pages"] = pages

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    # --- Отправляем первую страницу ---
    current_page = 0
    lines = []
    percent = (tol - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[current_page]:
        map_id = beatmap[0]
        lazer = beatmap[1].upper()
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        # сравниваем с базовыми
        def cmp_symbol(val, base):
            if val > base + 15:
                return "🔼"
            elif val < base - 15:
                return "🔽"
            else:
                return "🔅"

        symbols = "".join([            
            cmp_symbol(acc, acc_base),
            cmp_symbol(aim, aim_base),
            cmp_symbol(speed, speed_base),
        ])

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"http://myangelfujiya.ru/index.html?id={map_id}"

        line = f"{total_str}pts {symbols} [http://osu.p...]({url}) | [🔗]({url_2})   +{mods}"
        lines.append(line)
    line = """\n            🔼 — скилл карты больше твоего
            🔽 — твой скилл больше, карта легче
            🔅 — такой же скилл, как твой"""
    lines.append(line)
    text = "\n".join(lines)

    keyboard = create_pagination_keyboard(current_page, len(pages), user_id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=topic_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True

    )




#logs&startup
START_TIME = time.time()
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  
)
logger = logging.getLogger(__name__)
def cleanup_temp():
    for f in glob.glob(os.path.join(TEMP_DIR, "*.png")):
        try:
            os.remove(f)
        except:
            pass
atexit.register(cleanup_temp)
def cleanup_flags():
    flags_dir = os.path.join(BOT_DIR, "stats", "flags")
    
    if os.path.exists(flags_dir):
        for f in os.listdir(flags_dir):
            try:
                os.remove(os.path.join(flags_dir, f))
            except Exception:
                pass
    else:
        os.makedirs(flags_dir, exist_ok=True)      
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))
    
    #async
    app.add_handler(CommandHandler("mods", start_mods))
    app.add_handler(CommandHandler("mappers", start_mappers))

    app.add_handler(CommandHandler("profile", start_profile))
    app.add_handler(CommandHandler("p", start_profile))

    app.add_handler(CommandHandler("card", start_card))  
    app.add_handler(CommandHandler("c", start_card))  

    app.add_handler(CommandHandler("recent_fix", start_recent_fix))
    app.add_handler(CommandHandler("fix", start_recent_fix))
    app.add_handler(CommandHandler("f", start_recent_fix))   
    
    app.add_handler(CommandHandler("recent", start_rs))
    app.add_handler(CommandHandler("rs", start_rs))    
    app.add_handler(CommandHandler("r", start_rs))

    app.add_handler(CommandHandler("pc", start_compare_profile))    
 
    app.add_handler(CommandHandler("start", start_help))
    app.add_handler(CommandHandler("help", start_help))
      
    app.add_handler(CommandHandler("music", start_beatmap_audio))

    app.add_handler(CommandHandler("maps_skill", start_farm))
    app.add_handler(CommandHandler("ms", start_farm))
    
    app.add_handler(CommandHandler("average", start_average_stats))
    app.add_handler(CommandHandler("avg", start_average_stats))
    app.add_handler(CommandHandler("a", start_average_stats))

    app.add_handler(CommandHandler("nochoke", start_nochoke))
    app.add_handler(CommandHandler("n", start_nochoke))

    #TODO make async
    app.add_handler(CommandHandler("simulate", simulate))
    app.add_handler(CommandHandler("s", simulate))

    app.add_handler(CommandHandler("settings", settings_command_handler))  

    app.add_handler(CommandHandler("beatmaps", beatmaps))
    app.add_handler(CommandHandler("b", beatmaps))

    app.add_handler(CommandHandler("name", set_name))
    app.add_handler(CommandHandler("link", set_name))
    app.add_handler(CommandHandler("nick", set_name))
    app.add_handler(CommandHandler("osu", set_name))

    app.add_handler(CommandHandler("gn", random_image))    

    app.add_handler(CommandHandler("doubt", doubt))
    app.add_handler(CommandHandler("blacks", blacks))

    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("uptime", uptime))

    app.add_handler(CommandHandler("challenge", challenge))


    app.add_handler(CallbackQueryHandler(rs_button, pattern=r"^rs_"))
    app.add_handler(CallbackQueryHandler(button_handler_profile, pattern=r"^(profile|card|noop)$"))
    app.add_handler(CallbackQueryHandler(beatmaps_button_handler, pattern="^beatmaps_"))    
    app.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^settings_"))
    # app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(next_challenge|finish_challenge|leaderboard|info|skip_challenge|menu_challenge)$"))
    app.add_handler(CallbackQueryHandler(simulate_button_handler, pattern="^simulate_"))

    app.add_handler(CallbackQueryHandler(farm_pagination_callback, pattern=r"^farm_page:"))
    app.add_handler(CallbackQueryHandler(farm_step_callback, pattern=r"^farm_(skill|mod|lazer|tol):"))
    app.add_handler(CallbackQueryHandler(page_callback_choke, pattern=r"^page_\d+_\d+$"))
    
    app.add_handler(CommandHandler("reminders", reminders_command))

    class ShortNetworkHandler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if "NetworkError" in msg: print("NetworkError")
            else: print(msg)
    logger.addHandler(ShortNetworkHandler())
    cleanup_flags()

    try: app.run_polling()
    except NetworkError:  print("NetworkError")
if __name__ == "__main__":
    main()