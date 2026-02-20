


import aiohttp
import random
import asyncio
import temp
import re
import requests
from typing import List, Dict
from datetime import datetime
from collections import defaultdict

from .osu_http import get_score_page
from .osu_auth import get_osu_token
from modules.utils.network import fetch_with_timeout, post_with_timeout, try_request
from modules.utils.osu_conversions import is_legacy_score
from modules.systems.json_files import load_score_file, save_score_file

from config import OSU_ID_CACHE_FILE

TIMEOUT = 10

api_limit = asyncio.Semaphore(10)



async def get_user_profile_batch(usernames: list[str]) -> list[dict | None]:    
    token = await get_osu_token()

    async with api_limit:
        async with aiohttp.ClientSession() as session:
            print('🔻 API request (get_user_profile_batch)')
            tasks = []            
            for username in usernames:
                url = f"https://osu.ppy.sh/api/v2/users/{username}/osu"
                headers = {"Authorization": f"Bearer {token}"}
                tasks.append(fetch_with_timeout(session, url, headers))

            return await asyncio.gather(*tasks)        

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

            is_anime_bg = score.get('beatmapset', {}).get('anime_cover', False)

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
                "rank": score.get('rank', 'D'),
                "artist": score.get('beatmapset', {}).get('artist'),
                "time": score.get('created_at', ''),
                "is_anime_bg": is_anime_bg,
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
        print('🔻 API request (beatmap)')
        async with aiohttp.ClientSession() as session:
            async with api_limit:
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for beatmap_id '{beatmap_id}' failed: {e}")
        return None
    
async def get_beatmapset(beatmapset_id: int):
    url = f"https://osu.ppy.sh/api/v2/beatmapsets/{beatmapset_id}"
    token = await get_osu_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": "20240529",
        "Accept": "application/json"
    }
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        print('🔻 API request (get beatmapsets)')
        async with aiohttp.ClientSession() as session:
            async with api_limit:
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for '{beatmapset_id}' failed: {e}")
        return None
    
async def search_beatmapsets(text: str, cursor: str = None):
    params = {"q": text}
    if cursor:
        params['cursor_string'] = cursor

    url = f"https://osu.ppy.sh/api/v2/beatmapsets/search"
    token = await get_osu_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": "20240529",
        "Accept": "application/json"
    }
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        print('🔻 API request (search beatmapsets)')
        async with aiohttp.ClientSession() as session:
            async with api_limit:
                async with session.get(url, headers=headers, params=params, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Request for '{text}' failed: {e}")
        return None
    
async def search_profiles(text: str, page: int = 1):
    params = {
        "query": text,
        "mode": "user",
        "page": page
    }

    url = "https://osu.ppy.sh/api/v2/search"
    token = await get_osu_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": "20240529",
        "Accept": "application/json"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        print(f'🔻 API request (search profiles) page={page}')

        async with aiohttp.ClientSession() as session:
            async with api_limit:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()

    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Profile search for '{text}' failed: {e}")
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
            async with api_limit:
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
            async with api_limit:
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
    
async def _get_recent_scores(
    username: str,
    token: str = None,
    timeout_sec: int = 10,
    limit: int = 25,
    fails: int = 1,
    offset: int = 0,
    mode: str = 'osu',
    select: str = 'recent'):

    if token is None: token = await get_osu_token()

    user_id = await get_user_id(username, token)
    if not user_id:
        return None

    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": "20240529",
        "Accept": "application/json",
    }
    url_recent = f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/{select}?include_fails={fails}&limit={limit}&mode={mode}&offset={offset}"
    url_user_info = f"https://osu.ppy.sh/api/v2/users/{user_id}/{mode}"

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async def fetch(url):
                async with api_limit:
                    async with session.get(url, headers=headers) as resp:
                        return resp.status, await resp.json() if resp.status == 200 else None

            recent_task = fetch(url_recent)
            user_task = fetch(url_user_info)

            (status_recent, scores), (status_user, user_info) = await asyncio.gather(recent_task, user_task)

            if status_recent != 200:
                print(f"_get_recent_scores | recent failed: {status_recent}")
                scores = []

            if status_user != 200:
                print(f"_get_recent_scores | user_info failed: {status_user}")
                user_info = {}

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"_get_recent_scores: {e}")

    if not scores and not user_info:
        return None
    
    for score in scores:
        if score.get("id", 0) == 0:
            created_at = score.get("created_at", "unknown_time")
            safe_time = re.sub(r'[^\w\-]', '_', created_at)
            score["id"] = f"{user_id}_{safe_time}"   

    return {"scores": scores, "user_info": user_info}

async def _get_beatmap_scores(
    username: str,
    beatmap_id: str,
    limit: int = 25,
    fails: int = 25,
    mode: str = "osu",    
    timeout_sec: int = 10,):

    token = await get_osu_token()

    user_id = await get_user_id(username, token)
    if not user_id:
        return None

    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": "20240529",
        "Accept": "application/json",
    }
    url_scores = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}/scores/users/{user_id}/all?legacy_only=0&ruleset={mode}"
    url_beatmap = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}"
    url_user_info = f"https://osu.ppy.sh/api/v2/users/{user_id}/{mode}"

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async def fetch(url):
                async with api_limit:
                    async with session.get(url, headers=headers) as resp:
                        return resp.status, await resp.json() if resp.status == 200 else None

            scores_task = fetch(url_scores)
            map_task = fetch(url_beatmap)
            user_task = fetch(url_user_info)

            (status_scores, scores), (status_map, map), (status_user, user_info) = await asyncio.gather(
                scores_task, 
                map_task, 
                user_task
            )

            if status_scores != 200:
                print(f"_get_beatmap_scores | scores failed: {status_scores}")
                scores = []

            if status_map != 200:
                print(f"_get_beatmap_scores | map failed: {status_map}")
                map = []

            if status_user != 200:
                print(f"_get_beatmap_scores | user_info failed: {status_user}")
                user_info = {}

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"_get_beatmao_scores: {e}")

    if not scores and not user_info and not map:
        return None
    
    if isinstance(scores, dict) and "scores" in scores:
        scores = scores["scores"]
    
    for score in scores:
        if score.get("id", 0) == 0:
            created_at = score.get("created_at", "unknown_time")
            safe_time = re.sub(r'[^\w\-]', '_', created_at)
            score["id"] = f"{user_id}_{safe_time}"   

    return {"scores": scores, "user_info": user_info, "beatmap": map}


async def get_user_scores_by_beatmap(
    username: str,
    beatmap_id: str,
    limit: int = 25,
    fails: int = 1):

    data = await _get_beatmap_scores(username, beatmap_id, limit=limit, fails=fails)
    
    if data is None:
        scores = []
        user_info = {}
        beatmap = []
    else:
        scores = data.get('scores') or []
        user_info = data.get('user_info') or {}
        beatmap = data.get('beatmap') or []
        beatmapset = beatmap.pop('beatmapset')

    results = []
    async with aiohttp.ClientSession() as session:
        for i, score in enumerate(scores):
            score_id = str(score["id"])
            cached_entry = load_score_file(score_id)
            if not cached_entry:   
                score['beatmapset'] = beatmapset                  
                score['beatmap'] = beatmap  
        
                cached_entry = await score_to_schema(score, user_info)

                save_score_file(score_id, cached_entry)
                
            results.append(cached_entry)
    return results
    
async def get_user_scores(
        username: str,
        limit: int = 25,
        fails: int = 1,
        select: str = 'recent'
    ):

    data = await _get_recent_scores(username, limit=limit, fails=fails, select=select)
    
    if data is None:
        scores = []
        user_info = {}
    else:
        scores = data.get('scores') or []
        user_info = data.get('user_info') or {}


    scores_sorted = sorted(scores, key=lambda s: s['ended_at'])
    count_by_map = defaultdict(int)

    for s in scores_sorted:
        map_id = s['beatmap']['id']
        count_by_map[map_id] += 1
        s['try'] = count_by_map[map_id]

    scores_sorted.sort(key=lambda s: s['ended_at'], reverse=True)

    results = []
    async with aiohttp.ClientSession() as session:
        for i, score in enumerate(scores_sorted):
            score_id = str(score["id"])
            cached_entry = load_score_file(score_id)
            
            if cached_entry:
                if cached_entry['state']['error']:
                    print("cached_entry state error, override")

                    cached_entry = None
                
            if not cached_entry:            
                cached_entry = await score_to_schema(score, user_info)
              
                save_score_file(score_id, cached_entry)
                
            results.append(cached_entry)
    return results

async def score_to_schema(score, user_info):
    """
    создает json схему
    
    :param score: raw осу скор
    :param user_info: осу профиль

    """
    
    beatmap = score.get("beatmap", {})
    beatmapset = score.get("beatmapset", {})
    
    da_active = False
    speed_multiplier = None
    custom_values = {}
    mods_orig = score.get("mods", [])

    mods = score.get("mods", [])
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

    # mods_text = score.get("mods", "+".join(score.get("mods", [])) if score.get("mods") else "NM")
    
    fail = False
    if not score.get('passed'): fail = True

    statistics = score.get('statistics', {})
    maximum_statistics = score.get('maximum_statistics', {})
    
    return {
        "user": {
            "username":     user_info['username'],
            "total_pp":     user_info['statistics']['pp'],
            "country_rank": user_info['statistics']['country_rank'],
            "global_rank":  user_info['statistics']['global_rank'],
            "country_code": user_info['country_code'],
            
            "total_pp_cache": None,

            "avatar_url":   user_info.get('avatar_url'),
            "cover_url":    user_info.get('cover_url'),
        },
        "map": {
            "card2x_url":   beatmapset.get('covers', {}).get('card@2x'),
            "beatmap_full": f"{beatmapset.get('artist', '')} - {beatmapset.get('title', '')} [{beatmap.get('version', '')}]",            
            "mapper":       beatmapset.get("creator"),
            "beatmap_id":   beatmap.get("id"),

            "status":       beatmap.get("status"),
            "bpm":          beatmap.get("bpm"),
            "url":          beatmap.get("url"),
            "hit_length":   beatmap.get("hit_length"),
            "cs":           beatmap.get("cs"),
            "ar":           beatmap.get("ar"),
            "od":           beatmap.get("accuracy"),
            "hp":           beatmap.get("drain"),
        },
        "osu_api_data": {              
            "rank_legacy":      score.get("rank"),            
            "date":             score.get("created_at") or score.get("ended_at"),  
            "id":               score.get("id"),
            "best_id":          score.get("best_id")
        },
        "osu_score": {
            "user_id" :         score.get("user_id", score.get("user", {}).get("id")) or None,
            "score_legacy":     score.get("classic_total_score") or score.get("legacy_total_score") or 0,
            "score_lazer":      score.get("score") or 0,
            "mods":             mods_text,
            "accuracy":         score.get("accuracy"),
            "max_combo":        score.get("max_combo"),            
            "pp":               score.get("pp") or 0,
            "count_300":        statistics.get("great") or None,
            "count_100":        statistics.get("ok") or None,
            "count_50":         statistics.get("meh") or None,
            "count_miss":       statistics.get("miss") or None,           
            "ignore_hit":       statistics.get("ignore_hit") or None,
            "ignore_miss":      statistics.get("ignore_miss") or None,
            "small_bonus":      statistics.get("small_bonus") or None,
            "large_tick_hit":   statistics.get("large_tick_hit") or None,
            "large_tick_miss":  statistics.get("large_tick_miss") or None,            
            "slider_tail_hit":  statistics.get("slider_tail_hit") or None,
            "failed":           fail,
            "try_count":        score.get("try", 1),      
        },
        "neko_api_calc": {
            "pp":               None,
            "no_choke_pp":      None,
            "perfect_pp":       None,

            "star_rating":      None,
            "perfect_combo":    None,
            "expected_bpm":     None,
        },
        "lazer_data": {
            "ranked":           None,
            "total_score":      score.get("total_score"),
            "rank":             score.get("rank"),
            "speed_multiplier": speed_multiplier,            
            "DA_values":        custom_values,
                                        # возможно другие
        },
        'osu_statistics_max': {
            'great':            maximum_statistics.get('great', 0),
            'ignore_hit':       maximum_statistics.get('ignore_hit', 0),
            'large_tick_hit':   maximum_statistics.get('large_tick_hit', 0),
            'slider_tail_hit':  maximum_statistics.get('slider_tail_hit', 0),
        },
        "state": {            
            "lazer":            not is_legacy_score(score),
            "mode":             "osu",
            "calculated":       False,
            "ready":            False,
            "error":            False,
        },
        "meta": {
            "created_at":       datetime.now().isoformat(),
            "calculated_at":    None,
            "version":          "03022026",         # !
        }
    }

async def get_score_by_id(score_id: str, token: str, timeout_sec: int = 10, override: bool = False):
    if not override:    
        cached_entry = load_score_file(score_id)
    else: 
        cached_entry = False
    
    if not cached_entry:
        async with api_limit:
            async with aiohttp.ClientSession() as session:    

                data = await get_score_page(session, score_id, score_id, no_check=True)
                if not data:
                    return None

                user_info = await get_osu_user_additional_data(str(data["user"]["id"]), "osu", token)                
                cached_entry = await score_to_schema(data, user_info)

                save_score_file(score_id, cached_entry)

    return cached_entry



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
        async with api_limit:
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
            async with api_limit:
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
