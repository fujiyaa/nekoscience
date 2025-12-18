


import lxml.html, json, os, time, requests, zipfile, aiohttp, aiofiles, asyncio

from bot.src.modules.external.external_config import semaphore
from bot.src.config import BEATMAPS_DIR, CACHE_TTL

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