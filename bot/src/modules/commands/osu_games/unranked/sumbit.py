import os, json
from datetime import datetime, timedelta, timezone
SCORES_DIR = 'E:/fa/nekoscience/bot/src/scores_v4'
TIME_OPTIONS = [1, 2, 3, 6, 12, 24, 48]
CROSSCLIENT_OPTIONS = ["🔹Лазер", "🔸Стейбл"]

def get_score_path(score_id: str) -> str:
    return os.path.join(SCORES_DIR, f"{score_id}.json")
def load_score_file(score_id: str, ignore_empty: bool = False) -> dict | None:
    path = get_score_path(score_id)
    if not os.path.exists(path) and not ignore_empty:
        raise ValueError(f'⚠ Скора нет в кеше {score_id}')
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Ошибка при загрузке файла {score_id}: {e}")

    return None


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

class CancelSubmit(Exception):
    def __init__(self, incorrections_list=None):
        self.incorrections_list = incorrections_list

def submit(cached_entry: dict | None = None, match_entry: dict | None = None):
    try:       
        incorrections_list = []
        # если пустой то PASS в конце
        # либо набор того что не прошло и можно отобразить

        if not none_check(match_entry, 'match_entry'): return
        if not id_check(match_entry, 'match_entry'): return    
        
        # трекинг этого матча (отвечать ли сообщением)
        track = match_entry.get('track')
        if track is None:
            print(f'[submit] track is None')
            return
        if track is False:
            print(f'[submit] tracking is OFF')
            return

        # стейт матча
        match_state = match_entry.get('state')    
        if not match_state['started']:
            print(f'[submit] match_state: not started')
            incorrections_list.append('Матч: еще не начат')
            # FIXME здесь переключить трекинг на off
            raise CancelSubmit(incorrections_list)
        if match_state['finished']:
            print(f'[submit] match_state: finished')
            incorrections_list.append('Матч: уже завершен')
            # FIXME здесь переключить трекинг на off
            raise CancelSubmit(incorrections_list)
            
        # таймер
        match_config = match_entry.get('config')
        if match_config is None:
            print(f'[submit] match_config is None')
            return
        match_time = match_config.get('time')
        if type(match_time) != type(0):
            print(f'[submit] match_time: {match_time}')
            return    
        match_timer = timedelta(hours=TIME_OPTIONS[match_time])

        match_start_ts = match_entry.get('started_at')
        if not match_start_ts: 
            print(f'[submit] match_start_ts: {match_start_ts}')
            return
        started_ts = datetime.fromisoformat(match_start_ts)
        if not datetime.now(timezone.utc) - started_ts < match_timer:
            print(f'[submit] timer: exiting')
            incorrections_list.append('Таймер: время вышло')
            raise CancelSubmit(incorrections_list)

        # cached_entry
        if not none_check(cached_entry, 'cached_entry'): return
        osu_api_data = cached_entry.get('osu_api_data')
        if not id_check(osu_api_data, 'cached_entry'): return
        # score_id = str(osu_api_data.get('id'))

        # фейл    
        osu_score = cached_entry.get('osu_score')
        failed = osu_score.get('failed')
        if failed:
            print(f'[submit] score has fail: exiting')
            return
        
        # проверить карту    
        score_map_id = cached_entry.get('map').get('beatmap_id')
        if score_map_id is None:
            print(f'[submit] score_map_id is None')
            return
        match_intake = match_entry.get('intake')
        if match_intake is None:
            print(f'[submit] match_intake is None')
            return
        match_map_id = match_intake.get('map_id')
        if match_map_id is None:
            print(f'[submit] score_map_id is None')
            return
        if int(score_map_id) != int(match_map_id):
            print(f'[submit] map_id does not match')
            return
        
        # опредилить роль в матче из скора
        score_osu_id = osu_score.get('user_id')
        if not score_osu_id:
            print(f'[submit] score_user_id: {score_osu_id}')
            return
        creator_osu_id = match_entry.get('creator', {}).get('osu_id')
        member_osu_id = match_entry.get('member', {}).get('osu_id')
        if not creator_osu_id or not member_osu_id:
            print(f'[submit] creator or member is missing but should be known at that point (match started)')
            return
        
        if score_osu_id == creator_osu_id:
            role = 'creator'
        elif score_osu_id == member_osu_id:
            role = 'member'
        else:
            print(f'[submit] role is unknown: user {score_osu_id}')
            return

        # сабмитнула ли уже эта роль
        submit_state_result = match_entry.get('submit_state', {}).get(role)
        if submit_state_result is None:
            print(f'[submit] submit_state_result is None')
            return
        if submit_state_result:
            print(f'[submit] {role} already submitted, exiting')
            incorrections_list.append(f'У тебя уже был сабмитнут скор в этот матч')
            # FIXME здесь переключить трекинг на off
            raise CancelSubmit(incorrections_list)
        
        # проверить моды (+лазер DA если скор источник)    
        score_mods = osu_score.get('mods')
        if score_mods is None:
                print(f'[submit] score_mods is None, should be str')
                return
        
        match_source_is_score = match_config.get('source')
        if match_source_is_score:
            match_mods = match_intake.get('sent_mods')
            if match_mods is None:
                print(f'[submit] match_mods is None, should be str')
                return
            if type(score_mods) != type('') or type(match_mods) != type(''):
                print(f'[submit] mods should be str')
                return
            if score_mods != match_mods:
                print(f'[submit] mods does not match')
                incorrections_list.append(f'Моды: {score_mods}, а нужно {match_mods}')

            match_DA = match_intake.get('DA_values')
            if match_DA is None:
                pass
            else:
                score_DA = cached_entry.get('lazer_data', {}).get('DA_values')
                if score_DA is None:
                    print(f'[submit] score_DA is None, should be dict')
                    incorrections_list.append(f'Моды: в скоре из которого создан раунд, использован DA мод')
                if score_DA != match_DA:
                    print(f'[submit] DA values does not match')
                    incorrections_list.append(f'Моды: настройки DA не совпадают')
            
        else:
            # тут моды это лист []
            # incorrections_list ?
            # FIXME тут нужно умную функцию поиска модов в матче
            print(f'[submit] FIXME тут нужно умную функцию поиска модов в матче')
            return
        
        # клиент: 0 - стейбл, 1 - лазер
        match_client = match_config.get('crossclient')
        if match_client is None:
            print(f'[submit] match_client is None')
            return
        score_client = cached_entry.get('state').get('lazer')
        if score_client is None:
            print(f'[submit] score_client is None')
            return
        if bool(score_client) != bool(match_client):
            print(f'[submit] clients does not match')
            incorrections_list.append(f'Клиент: должен быть {CROSSCLIENT_OPTIONS[match_client]}')
        
        # получить условие победы из скора
        # 
        #     "🆕 SCORE-V2",    0
        #     "👨‍🦳 SCORE-STD",   1
        #     "🏹 Точность",    2
        #     "❌ Миссы",       3
        #     "🔗 Комбо"        4
        #
        match_goal = match_config.get('goal')
        if match_goal is None:
            print(f'[submit] match_goal is None')
            return
        if match_goal == 0:
            score_goal_data = cached_entry.get('lazer_data', {}).get('total_score')
        elif match_goal == 1:
            score_goal_data = cached_entry.get('osu_score', {}).get('score_legacy')
        elif match_goal == 2:
            score_goal_data = cached_entry.get('osu_score', {}).get('accuracy')
        elif match_goal == 3:
            score_goal_data = cached_entry.get('osu_score', {}).get('count_miss')
        elif match_goal == 4:
            score_goal_data = cached_entry.get('osu_score', {}).get('max_combo')
        else:
            print(f'[submit] match_goal index is unknown: {match_goal}')
            return
        if score_goal_data is None:
            print(f'[submit] score_goal_data is None')
            return
        
        
        if len(incorrections_list) < 1:
            print(f'[submit] PASS')

            # записать score_goal_data в role
            # обновить стейты

        else:
            raise CancelSubmit(incorrections_list)

    except CancelSubmit as c:
        if c.incorrections_list:
            print(f'[submit] CancelSubmit')
            print(f"скор нельзя сабмитнуть по причине:")
            for item in incorrections_list:
                print(f"- {item}")
        else:
            print(f'[submit] CancelSubmit without description')
            return
    except Exception as e:
        print(e)



match = {
    "started_at": "2026-05-20T09:04:08.982298+00:00",   # НОВОЕ ПОЛЕ
    "track": True,      # трекинг этого матча (отвечать ли сообщением)
    "submit_state": {                                             
      "creator": False,
      "member": False,
    },
    "submit_result": {                                             
      "creator": None,
      "member": None
    },                                              # НОВОЕ ПОЛЕ

    "config": {
      "crossclient": 1,
      "goal": 0,
      "mods": [],
      "source": 1,
      "time": 3
    },
    "created_at": 1778930985,    
    "creator": {
      "osu_id": 11596989,
      "osu_name": "Fujiya",
      "tg_id": 1803166423,
      "tg_name": "fujiya_sama"
    },
    "id": "115969891778930985",
    "intake": {
      "map_full": "Oratorio The World God Only Knows - God only knows -Secrets of the Goddess- [The World Guy Only Knows]",
      "map_id": "5274323",
      "sent_id": 4287518921,
      "sent_mods": "DT+DA",
      "DA_values": {
        "circle_size": 3,
        "approach_rate": 8.7, 
      },
      "sent_type": "score",
      "temp_rank": "1"
    },
    "member": {
      "osu_id": 26197609,
      "osu_name": "foundbpm",
      "tg_id": 7354740126,
      "tg_name": "foundbpm"
    },
    "pending_joins": [],
    "state": {
      "finished": False,
      "started": True,
      "winner": None
    }
}
cached_entry = None
try: cached_entry = load_score_file('6711851789')
except: pass

submit(cached_entry, match)