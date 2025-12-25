


import aiohttp
import random
import asyncio
import temp
import re
import requests
from typing import List, Dict

from .osu_http import get_score_page, enrich_score_lazer
from .osu_auth import get_osu_token
from modules.utils.network import fetch_with_timeout, post_with_timeout, try_request
from modules.utils.osu_conversions import is_legacy_score
from modules.systems.json_files import load_score_file, save_score_file

from config import OSU_ID_CACHE_FILE



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

async def get_score_by_id(score_id: str, token: str, timeout_sec: int = 10):
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



# это нигде не исопользуется???

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

async def get_beatmapset_id_from_md5(md5_hash: str, token: str) -> int:
    if token is None:
        token = await get_osu_token()
    url = f"https://osu.ppy.sh/api/v2/beatmaps/lookup?checksum={md5_hash}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["beatmapset_id"]

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
                    "beatmapset_id": beatmapset["id"],

                    "artist": beatmapset["artist"],
                    "title": beatmapset["title"],
                    "creator": beatmapset["creator"],                    
                    "bg_url": beatmapset['covers']['card']
                }

        return None
    
async def check_osu_challenge_completed(user_osu_id: int, beatmapset_id: int, goal: dict) -> bool:
    try:
        token = await get_osu_token()
        url = f"https://osu.ppy.sh/api/v2/users/{user_osu_id}/scores/recent?limit=1"
        headers = {"Authorization": f"Bearer {token}"}
        
        print('🔻 API request (check_osu_challenge_completed)')
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return False
                scores = await resp.json()

        if not scores:
            return False

        score = scores[0]

        if score['beatmapset']['id'] != beatmapset_id:
            return False

        goal_type = goal.lower()

        # ranks_order = ["F", "D", "C", "B", "A", "S", "SH", "SS", "SSH"]
        player_rank = score.get("rank", "F")
        # player_rank_index = ranks_order.index(player_rank) if player_rank in ranks_order else 0
        acc = score.get("accuracy", 0.0) * 100
        mods = score.get("mods", [])
        if isinstance(mods, str):
            mods = [mods]

        if goal_type == "пройти на s (full combo)":
            # S, SH, SS или SSH (S с FC)
            if player_rank not in ("S", "SH", "SS", "SSH"):
                return False

        elif goal_type == "пройти на а (90%+ accuracy)":
            if  acc <= 90:
                return False

        elif goal_type == "пройти на в (80%+ accuracy)":
            if  acc <= 80:
                return False

        elif goal_type == "пройти на с (70%+ accuracy)":
            if  acc <= 70:
                return False

        elif goal_type == "пройти с модом sd":
            if "SD" not in mods:
                return False

        elif goal_type == "пройти с модом hd":
            if "HD" not in mods:
                return False

        elif goal_type == "пройти с модом hr":
            if "HR" not in mods:
                return False

        elif goal_type == "пройти с модом dt или hr":
            if not ("DT" in mods or "HR" in mods):
                return False

        elif goal_type == "просто пройти карту":
            if player_rank == "F":
                return False

        else:
            return False

        if "NF" in mods:
            return False

        return True
    except Exception as e:
        print(f"ошибка in check_osu_challenge_completed {e}")
        return False
