


import os, datetime
import bot.src.modules.external.localapi as localapi

file_p = "file_osu_pending"
file_v = "file_osu_verified"

async def _fetch(key: str):
        path = os.getenv(key)
        if not path:
            return {}
        resp = await localapi.read_file_neko(key)
        data = resp.get("current", {})
        return data if isinstance(data, dict) else {}

async def get_all_osu_verified():
    return await _fetch(file_v)

async def check_osu_verified(telegram_id: str):
    verified = await _fetch(file_v)    
    return verified.get(telegram_id, {}).get("osu_username")

async def verify_osu_user(text: str, telegram_id: str):    
    pending = await _fetch(file_p)
    new_verified = {}

    if text in pending:
        code_data = pending[text]
        osu_id = code_data["osu_id"]
        username = code_data["username"]
        created_at = code_data["created_at"]            
        now = datetime.datetime.utcnow()

        new_verified = {
            telegram_id: {
                "osu_id": osu_id, 
                "osu_username": username,
                "code_created": created_at,
                "verified": now.isoformat()
            }            
        }

        verified = await _fetch(file_v)

        keys_to_remove = []

        for k, v in verified.items():
            if k == telegram_id:
                keys_to_remove.append(k)
        if keys_to_remove:
            await localapi.remove_from_file_neko(file_v, keys_to_remove)

        
        for k, v in pending.items():
            if v.get("osu_id") == osu_id:
                keys_to_remove.append(k)
        if keys_to_remove:
            await localapi.remove_from_file_neko(file_p, keys_to_remove)

        response = await localapi.insert_to_file_neko(file_v, new_verified)  

        return username
    return False   
