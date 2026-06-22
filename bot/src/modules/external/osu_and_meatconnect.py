


import os
import zipfile
import aiohttp
import aiofiles
import asyncio
import traceback

from config import MAX_CONCURRENT_REQUESTS
from .osu_api import get_beatmap

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS) 

MAX_OSZ_SIZE = 50 * 1024 * 1024  # 25 MB



class OversizedFileError(Exception):
    pass

async def _try_download(
    session: aiohttp.ClientSession,
    url: str,
    osz_path: str,
    chunk_size: int
):
    print(f"[DOWNLOAD TRY] {url}")

    async with session.get(url, allow_redirects=True) as resp:
        print(f"[HTTP] status={resp.status}")

        if resp.status != 200:
            raise ValueError(f"[HTTP ERROR] status={resp.status}")

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            raise ValueError("[ERROR] HTML received instead of OSZ")
        
        size_header = resp.headers.get("Content-Length")
        if size_header and int(size_header) > MAX_OSZ_SIZE:
           raise OversizedFileError(f"OSZ exceeds {MAX_OSZ_SIZE} bytes")

        total = 0

        async with aiofiles.open(osz_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(chunk_size):
                if not chunk:
                    continue

                total += len(chunk)

                if total > MAX_OSZ_SIZE:
                    print(f"[ABORT] file too large: {total} bytes")
                    raise OversizedFileError(f"OSZ exceeds {MAX_OSZ_SIZE} bytes")

                await f.write(chunk)

        print(f"[DOWNLOAD COMPLETE] bytes={total}")


def _extract_osz(osz_path: str, extract_dir: str):
    print(f"[EXTRACT] start: {osz_path} -> {extract_dir}")

    if not os.path.exists(osz_path):
        raise FileNotFoundError(
            f"osz missing before extract: {osz_path}"
        )

    with zipfile.ZipFile(osz_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print("[EXTRACT] done")

    try:
        os.remove(osz_path)
        print(f"[CLEANUP] removed {osz_path}")
    except Exception:
        print("[ERROR] failed to remove osz")
        traceback.print_exc()


async def download_osz_async(
    mapset_id: int,
    osu_session: str,
    save_dir: str,
    override: bool = False,
    connect_timeout: int = 5,
    read_timeout: int = 60,
    chunk_size: int = 8192
):
    extract_dir = os.path.join(save_dir, str(mapset_id))
    osz_path = os.path.join(save_dir, f"{mapset_id}.osz")
    final_mapset_id = mapset_id

    try:
        print(f"[START] mapset_id={mapset_id}")
        print(f"[PATH] extract_dir={extract_dir}")

        # cache
        if is_valid_mapset_folder(extract_dir) and not override:
            print(f"[CACHE HIT] using existing mapset: {extract_dir}")

            return {
                "mapset_id": final_mapset_id,
                "path": extract_dir
            }

        os.makedirs(save_dir, exist_ok=True)
        print(f"[DIR OK] save_dir exists: {save_dir}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": f"https://osu.ppy.sh/beatmapsets/{mapset_id}"
        }

        cookies = {
            "osu_session": osu_session
        }

        timeout = aiohttp.ClientTimeout(
            sock_connect=connect_timeout,
            sock_read=read_timeout
        )

        download_urls = [
            f"https://osu.ppy.sh/beatmapsets/{mapset_id}/download",
            f"https://beatconnect.io/b/{mapset_id}"           
        ]

        download_success = False
        last_error = None

        async with aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            cookies=cookies
        ) as session:

            for url in download_urls:
                try:
                    await _try_download(
                        session=session,
                        url=url,
                        osz_path=osz_path,
                        chunk_size=chunk_size
                    )

                    download_success = True
                    break

                except OversizedFileError as e:
                    print("[HARD STOP] file too large, skipping fallback")
                    raise e

                except Exception as e:
                    last_error = e

                    print(f"[DOWNLOAD FAILED] {url}")
                    traceback.print_exc()

                    # cleanup broken file
                    try:
                        if os.path.exists(osz_path):
                            os.remove(osz_path)
                            print(f"[CLEANUP] removed broken file")
                    except Exception:
                        traceback.print_exc()

        if not download_success and not isinstance(last_error, OversizedFileError):

            print("[FALLBACK] trying beatmap -> beatmapset conversion")

            beatmap_data = await get_beatmap(mapset_id)

            if beatmap_data:
                converted_mapset_id = (
                    beatmap_data.get("beatmapset_id")
                )

                if converted_mapset_id:
                    final_mapset_id = converted_mapset_id

                    print(
                        f"[FALLBACK SUCCESS] "
                        f"beatmap_id={mapset_id} "
                        f"-> beatmapset_id={converted_mapset_id}"
                    )

                    # рекурсивный retry
                    return await download_osz_async(
                        mapset_id=converted_mapset_id,
                        osu_session=osu_session,
                        save_dir=save_dir,
                        override=override,
                        connect_timeout=connect_timeout,
                        read_timeout=read_timeout,
                        chunk_size=chunk_size
                    )

            raise RuntimeError(
                f"All download sources failed for mapset {mapset_id}"
            ) from last_error


        size = os.path.getsize(osz_path)
        print(f"[FILE] size={size} bytes")

        os.makedirs(extract_dir, exist_ok=True)

        await asyncio.to_thread(
            _extract_osz,
            osz_path,
            extract_dir
        )

        if not os.path.exists(extract_dir):
            raise FileNotFoundError(
                f"[CRITICAL] extract_dir missing: {extract_dir}"
            )

        try:
            files = os.listdir(extract_dir)
            print(f"[RESULT] files in dir: {len(files)}")
        except Exception:
            print("[ERROR] cannot list extracted dir")
            traceback.print_exc()

        print(f"[SUCCESS] returning {extract_dir}")

        return {
            "mapset_id": final_mapset_id,
            "path": extract_dir
        }

    except Exception:
        print(f"[FATAL ERROR] mapset_id={mapset_id}")
        traceback.print_exc()
        raise

def is_valid_mapset_folder(path: str) -> bool:
    if not os.path.exists(path):
        return False

    files = os.listdir(path)

    return any(f.endswith(".osu") for f in files)