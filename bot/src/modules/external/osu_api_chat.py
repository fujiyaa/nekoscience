


import requests
import uuid

from config import OSU_PROFILE_ACCESS_TOKEN

API_BASE = "https://osu.ppy.sh/api/v2"
MAX_ATTEMPTS = 3



def send_pm(target_id: int, message: str, action: bool = False):
    headers = {
        "Authorization": f"Bearer {OSU_PROFILE_ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    for _attempt in range(1, MAX_ATTEMPTS + 1):
        resp = requests.post(
            f"{API_BASE}/chat/new",
            headers=headers,
            json={
                "target_id": target_id,
                "message": message,
                "is_action": action,
                "uuid": str(uuid.uuid4())
            }
        )
        resp.raise_for_status()    

        return resp.json()    
