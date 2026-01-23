


import lxml.html 
import json 
import os
import time
import requests
import zipfile
import aiohttp
import aiofiles
import asyncio
from datetime import datetime

from ..systems.json_files import load_score_file, save_score_file

from config import CACHE_TTL, LXML_TIMEOUT
from config import BEATMAPS_DIR, STATS_BEATMAPS, MAX_CONCURRENT_REQUESTS

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS) 



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
                            # cached_entry = {"raw": data, "processed": {}, "ready": False}
                            # save_score_file(score_id, cached_entry)

                            # я не знаю почему оно закомментировано но не надо трогать

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

async def enrich_score_lazer(session, user_id: str, cached_entry: dict, preloaded_page = None):  
    
    if preloaded_page is None:    
        if not cached_entry['state']['lazer']:
            cached_entry['state']['enriched'] = True 
            return cached_entry
    
    if cached_entry['state']['ready']: 
        return cached_entry
    
    if cached_entry['state']['enriched']:

        # сделать тут проверку, если давно то пересчитать        
        return cached_entry
        
    if not preloaded_page:
        score_page = await get_score_page(session, user_id, cached_entry['osu_api_data']['id'])
        mods_orig = cached_entry['osu_score']['mods']
    else: 
        score_page = preloaded_page
        mods_orig = score_page.get("mods", [])

    # хмм есть же is legacy
    # if not score_page:
    #     cached_entry['state']['ready'] = True
    #     save_score_file(score_id, cached_entry)
    #     return
    # lazer = True

    da_active = False
    speed_multiplier = None
    custom_values = {}

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
    
    accuracy = score_page.get("accuracy")
    rank = score_page.get("rank")
    total_score = score_page.get("total_score")
    ranked = score_page.get("ranked")
    
    _passed = score_page.get('passed', False)
    stats = score_page.get('statistics')
    if stats:
        cached_entry.setdefault("osu_score", {}).update(
            {
                'count_100': stats.get('ok'),
                'count_50': stats.get('meh'),
                'count_miss': stats.get('miss'),
                'count_300': stats.get('great'),
                'ignore_hit': stats.get('ignore_hit'),
                'ignore_miss': stats.get('ignore_miss'),
                'small_bonus': stats.get('small_bonus'),
                'large_tick_hit': stats.get('large_tick_hit'),
                'large_tick_miss': stats.get('large_tick_miss'),
                'slider_tail_hit': stats.get('slider_tail_hit'),
            }
        )

    mods_clean = []
    if mods_orig:       
        if isinstance(mods_orig[0], dict):
            mods_clean = [m for m in mods_orig if m.get("acronym") != "DA"]
            # CL
            if preloaded_page is not None:
                mods_clean = [m for m in mods_clean if m.get("acronym") != "CL"]
            mods_text = "+".join(m.get("acronym", "") for m in mods_clean if "acronym" in m)
        else:
            mods_clean = [m for m in mods_orig if m != "DA"]
            if preloaded_page is not None:
                mods_clean = [m for m in mods_clean if m != "CL"]
            mods_text = "+".join(mods_clean)
    else:
        mods_text = "NM"

    if speed_multiplier:
        mods_text += f" ({speed_multiplier}x)"
    if da_active:
        mods_text = mods_text + "+DA" if mods_text != "NM" else "+DA"

        

    cached_entry.setdefault("osu_score", {}).update(
            {
                "mods": mods_text,
            }
        )
    cached_entry.setdefault("lazer_data", {}).update(
            {
                "DA_values": custom_values, 
                "accuracy": accuracy, 
                "speed_multiplier": speed_multiplier, 
                "total_score": total_score, 
                "rank": rank,
                "ranked": ranked,
            }
        )    
    cached_entry.setdefault("state", {}).update(
            {
                "enriched": True, 
                # "lazer": is_lazer,
            }
        )
    cached_entry.setdefault("meta", {}).update({"enriched_at": datetime.now().isoformat()})

   

    return cached_entry

async def cache_remaining_scores(user_id: str, scores: list):
    async with aiohttp.ClientSession() as session:
        for s in scores[1:]:
            score_id = str(s['osu_api_data']['id'])
            cached_entry = load_score_file(score_id)

            if not cached_entry['state']['enriched']:
                cached_entry = await enrich_score_lazer(session, user_id, cached_entry)
                save_score_file(score_id, cached_entry)

            await asyncio.sleep(LXML_TIMEOUT)

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

async def beatmap(map_id: int) -> tuple[str | None, dict]:
    path_to_map = os.path.join(BEATMAPS_DIR, f"{map_id}.osu")

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

async def fetch_beatmap_data(beatmap_url, cache_expire_sec=3600, retries=3, timeout_sec=10):    
    beatmap_id = beatmap_url.rstrip("/").split("/")[-1]
    cache_path = f"{STATS_BEATMAPS}/{beatmap_id}.json"

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

async def download_osz_async(mapset_id: int, osu_session: str, save_dir: str, override: bool = True,
                             connect_timeout: int = 5, read_timeout: int = 60, chunk_size: int = 8192):
    extract_dir = os.path.join(save_dir, str(mapset_id))
    
    if os.path.exists(extract_dir):
        print(f"cache {extract_dir}")
        
        if not override:
            print(f"override {extract_dir}")
            return extract_dir

    os.makedirs(save_dir, exist_ok=True)

    url = f"https://beatconnect.io/b/{mapset_id}"
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