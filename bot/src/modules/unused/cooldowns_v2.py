


from datetime import datetime, timezone, timedelta
from pathlib import Path
import aiofiles
import asyncio
import json
import os

from config import USAGE_FILE, ACTIONS_COOLDOWNS, DEFAULT_COOLDOWN_V2

_file_lock = asyncio.Lock()



async def is_user_on_cooldown(
    service: str,
    action: str,
    user_id: int
) -> int:

    if not service or not action:
        return 0

    try:
        async with _file_lock:
            data = await _get_usage()

            user_key = str(user_id)
            last_used_iso = (
                data
                .get(service, {})
                .get(action, {})
                .get(user_key)
            )

            cooldown_seconds = _get_cooldown_seconds(service, action)

            if last_used_iso:
                remaining = _get_remaining_seconds(
                    last_used_iso,
                    cooldown_seconds
                )
                if remaining > 0:
                    return remaining

            _update_usage(data, service, action, user_key)
            await _set_usage(data)

    except Exception as e:
        print(f"[Cooldown Error] {e}")
        return 0

    return 0

def _get_cooldown_seconds(service: str, action: str) -> int:
    service_cfg = ACTIONS_COOLDOWNS.get(service, {})
    return (
        service_cfg.get(action)
        or service_cfg.get("default")
        or DEFAULT_COOLDOWN_V2
    )

def _get_remaining_seconds(
    last_used_iso: str,
    cooldown_seconds: int
) -> int:

    try:
        last_used = datetime.fromisoformat(last_used_iso)
    except Exception:
        return 0

    now = datetime.now(timezone.utc)
    elapsed = now - last_used
    cooldown_delta = timedelta(seconds=cooldown_seconds)

    if timedelta(0) <= elapsed < cooldown_delta:
        return int((cooldown_delta - elapsed).total_seconds())

    return 0

def _update_usage(
    data: dict,
    service: str,
    action: str,
    user_key: str
):
    service_data = data.setdefault(service, {})
    action_data = service_data.setdefault(action, {})
    action_data[user_key] = datetime.now(timezone.utc).isoformat()


async def _get_usage() -> dict:
    try:
        if not os.path.exists(USAGE_FILE):
            return {}

        async with aiofiles.open(USAGE_FILE, "r", encoding="utf-8") as f:
            raw = await f.read()

        if not raw.strip():
            return {}

        return json.loads(raw)

    except json.JSONDecodeError:
        return {}

    except Exception as e:
        print(f"[Read Usage Error] {e}")
        return {}

async def _set_usage(data: dict):
    try:
        Path(USAGE_FILE).parent.mkdir(parents=True, exist_ok=True)

        temp_file = str(USAGE_FILE) + ".tmp"

        async with aiofiles.open(temp_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=4))

        os.replace(temp_file, USAGE_FILE)

    except Exception as e:
        print(f"[Write Usage Error] {e}")
