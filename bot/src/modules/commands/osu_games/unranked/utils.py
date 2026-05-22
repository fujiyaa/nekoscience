


import html

from ....systems.json_files import load_score_file
from ....external.osu_http import get_beatmap_title_from_file_offline



def none_check(entry: dict | None = None, probe_name: str = '') -> bool:
    try:
        if entry is None or entry == '{}':
            print(f'[submit] {probe_name} failed: {entry}')
            raise
        else:
            return True
    except:
        return False

def id_check(entry: dict | None = None, probe_name: str = '') -> bool:
    try:
        id = str(entry.get('id'))
        if not id or type(id) != type(''):
            print(f'[submit] {probe_name} id failed: {id}')
            raise
        else: 
            print(f'[submit] {probe_name}: {id}')
            return True
    except:
        return False
    
def normalize_mods(mods):
    if mods is None:
        return None

    if isinstance(mods, str):
        result = {
            mod.strip().upper()
            for mod in mods.split('+')
            if mod.strip()
        }
        return result

    if isinstance(mods, list):
        result = {
            str(mod).strip().upper()
            for mod in mods
            if str(mod).strip()
        }
        return result

    return None

async def get_intake_text(intake: dict | None = None) -> str:
    none_text = "<code>- создание: нет контекста</code>"
    
    def c_text(title: str):
        return f"<code>+ создание: из {html.escape(title)}</code>"

    if intake is None: return none_text

    try:
        sent_type = str(intake['sent_type'])
        sent_id = int(intake['sent_id'])

    except:
        return none_text

    if sent_type == 'map':

        return c_text(await get_beatmap_title_from_file_offline(sent_id))

    elif sent_type == 'score':
        try:
            cached_entry = load_score_file(sent_id)

            map_id = int(cached_entry.get('map').get('beatmap_id'))

            return c_text(await get_beatmap_title_from_file_offline(map_id))
        except:
            return none_text
    else: 
        return none_text