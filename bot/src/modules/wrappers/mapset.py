


import html



async def get_map_text(cached_entry: dict = None): 
    map = cached_entry.get('map')
    osu_score = cached_entry.get('osu_score')
    neko_api_calc = cached_entry.get('neko_api_calc')
    stars = neko_api_calc.get('star_rating')    

    beatmap_escaped = html.escape(map.get('beatmap_full'))
    
    try_count = osu_score.get('try_count')
    try_text = ''
    if try_count > 1:
        try_text = f"<i><b>- Try #{try_count}</b></i>"

    map_id = map.get('beatmap_id')
    map_url = f"https://osu.ppy.sh/b/{map_id}"
    map_text = f'<a href="{map_url}">{beatmap_escaped} [{stars:.2f}★]</a> {try_text}'

    return map_text

async def get_mapset_link(cached_entry: dict = None): 
    map = cached_entry.get('map')
    status = map.get('status')
    mapper = map.get("mapper")

    map_id = map.get('beatmap_id')
    map_url = f"https://osu.ppy.sh/b/{map_id}"
    direct_link = f'<a href="https://myangelfujiya.ru/darkness/direct?id={map_id}">🔗</a>'
    mapper_link = f'<a href="https://osu.ppy.sh/users/{mapper}">by {mapper}</a>'
    mapset_link = f'⦿ <a href="{map_url}">Mapset</a> {mapper_link} • {status.capitalize()}  {direct_link}'

    return mapset_link
