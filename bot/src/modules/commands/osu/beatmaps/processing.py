


import os
import asyncio
import json

from ....external.osu_http import fetch_beatmap_data

from config import QUEUE_FILE, FLAG_FILE, STATS_BEATMAPS
from config import GROUPS_DIR, URL_SCAN_TIMEOUT



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
    todo_path = os.path.join(GROUPS_DIR, f"{group_id}.todo")
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if not os.path.exists(todo_path) and not os.path.exists(done_path):
        return "not_found"
    elif os.path.exists(done_path):
        return "done"
    else:
        return "in_progress"

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

async def delete_done_file(group_id: str):
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if os.path.exists(done_path):
        try:
            os.remove(done_path)
            print(f"✅ Файл {group_id}.done успешно удалён.")
        except Exception as e:
            print(f"❌ Ошибка при удалении файла {group_id}.done: {e}")
    else:
        print(f"⚠️ Файл {group_id}.done не найден.")

