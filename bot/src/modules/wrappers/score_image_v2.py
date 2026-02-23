


from ..systems.translations import SCORE_CAPTION as T



async def get_score_caption(cached_entry: dict, language: str = 'ru') -> str:
    l = language
    osu_api_data = cached_entry.get('osu_api_data', {})
    score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
    map_id = cached_entry.get('map', {}).get('beatmap_id')
    map_url = f"https://osu.ppy.sh/b/{map_id}"
    username = cached_entry.get('user', {}).get('username')
    profile_url = f"https://osu.ppy.sh/u/{username}"

    return (
        f"<b><a href='{profile_url}'>{T.get('Profile')[l]}</a></b>  •   "
        f"<b><a href='{score_url}'>{T.get('Score')[l]}</a></b>   •   "          
        f"<b><a href='{map_url}'>{T.get('Beatmap')[l]}</a></b>   •   "
        f"id<code>{map_id}</code>"
    )
