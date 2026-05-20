import os, json
from datetime import datetime, timedelta, timezone

SCORES_DIR = 'E:/fa/nekoscience/bot/src/scores_v4'
TIME_OPTIONS = [1, 2, 3, 6, 12, 24, 48]
CROSSCLIENT_OPTIONS = ["🔹Лазер", "🔸Стейбл"]
GOAL_OPTIONS = [
    "🆕 SCORE-V2",
    "👨‍🦳 SCORE-STD",
    "🏹 Точность",
    "❌ Миссы",
    "🔗 Комбо"
]

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

class CancelTryFinish(Exception):
    def __init__(self, list=None, forward_list_back=None, finished=None):
        self.list = list
        self.forward_list_back = forward_list_back
        self.finished = finished

def submit(cached_entry: dict | None = None, match_entry: dict | None = None) -> str | None:
    try:       
        incorrections_list = []
        # если пустой то PASS в конце
        # либо набор того что не прошло и можно отобразить

        if not none_check(match_entry, 'match_entry'): return
        if not id_check(match_entry, 'match_entry'): return    
        
        # трекинг этого раунда (отвечать ли сообщением)
        track = match_entry.get('track')
        if track is None:
            print(f'[submit] track is None')
            return
        if track is False:
            print(f'[submit] tracking is OFF')
            return

        # стейт раунда
        match_state = match_entry.get('state')    
        if not match_state['started']:
            print(f'[submit] match_state: not started')
            incorrections_list.append('Раунд: еще не начат')
            # FIXME как так может быть
            raise CancelSubmit(incorrections_list)
        if match_state['finished']:
            print(f'[submit] match_state: finished')
            incorrections_list.append('Раунд: уже завершен')
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
            incorrections_list.append(f'Фейл: карта не пройдена')
        
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
        
        # опредилить роль в раунде из скора
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
            incorrections_list.append(f'У тебя уже был сабмитнут скор в этот раунд')
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
                    # incorrections_list.append(f'Моды: DA мод не найден, а матч создан с этим модом')
                if score_DA != match_DA:
                    print(f'[submit] DA values does not match')
                    incorrections_list.append(f'Моды: настройки DA должны были быть:')
                    for item in match_DA:
                        incorrections_list.append(f'{item} = {match_DA[item]}')
            
        else:
            # тут моды это лист []
            # incorrections_list ?
            # FIXME тут нужно умную функцию поиска модов в раунде
            print(f'[submit] FIXME тут нужно умную функцию поиска модов в раунде')
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
            match_entry['submit_state'][role] = True
            match_entry['submit_result'][role] = float(score_goal_data)
            
            # здесь сразу нужно завершать раунд, возможно
            finish_list, match_finished = match_try_finish(match_entry)

            # считать рейтинги
            if match_finished:
                match_entry['state']['finished'] = True

                ratings = process_elo(match_entry)

                if ratings is not None:
                    print('[submit] new ratings calculated')

                    ratings_text = (
                        f"{ratings['creator_elo_new']} ({ratings['creator_delta']:+d})\n"
                        f"{ratings['member_elo_new']} ({ratings['member_delta']:+d})"
                    )

                    match_entry['state']['elo_calculated'] = True
                else:
                    ratings_text = 'ошибка при рассчете рейтинга'

                    print('[submit] error in ratings calculation')


            

            # сохранить!!!!!
            ################## FIXME
            # # #  #


            text = ''
            # финальный текст сообщения            
            if match_finished:
                text+=(f'Скор сабмитнут, раунд завершен:\n')                
                text+=(f'Цель была: {GOAL_OPTIONS[match_goal]}\n')
                text+=(f"{match_entry['submit_result']['creator']} vs {match_entry['submit_result']['member']}\n")
                for item in finish_list:
                    text+=(f"- {item}\n")
                text+=(ratings_text)
            else:
                text+=(f'Скор сабмитнут, однако раунд не завершен:')
                for item in finish_list:
                    text+=(f"\n- {item}")

            return(text)
        else:
            raise CancelSubmit(incorrections_list)

    except CancelSubmit as c:
        if c.incorrections_list:
            print(f'[submit] CancelSubmit')
            text = (f"Скор нельзя сабмитнуть по причине:")
            for item in incorrections_list:
                text += (f"\n- {item}")

            return text
        else:
            print(f'[submit] CancelSubmit without description')
            return
    except Exception as e:
        print(e)

def match_try_finish(match_entry: dict | None = None):    
    # таймер должен быть проверен заранее
    # match_entry должен быть проверен
    list = []
    finished = False
    try:
        # стейт раунда
        match_state = match_entry.get('state')    
        if not match_state['started']:
            list.append('Раунд: еще не начат')
            raise CancelTryFinish(list)
        if match_state['finished']:
            list.append('Раунд: уже завершен')
            raise CancelTryFinish(list)
        
        submit_state = match_entry.get('submit_state')
        if submit_state is None:
            list.append('submit_state is None')
            raise CancelTryFinish(list)

        submit_result = match_entry.get('submit_result')
        if submit_result is None:
            list.append('submit_result is None')
            raise CancelTryFinish(list)

        creator_state = submit_state.get('creator')
        creator_result = submit_result.get('creator') # 0.0 default
        member_state = submit_state.get('member')        
        member_result = submit_result.get('member') # 0.0

        if not creator_state:
            list.append('Создатель раунда еще не играл')
            raise CancelTryFinish(list, True, False)
        if not member_state:
            list.append('Участник раунда еще не играл')
            raise CancelTryFinish(list, True, False)
        

        # условие победы
        # 
        #     "🆕 SCORE-V2",    0
        #     "👨‍🦳 SCORE-STD",   1
        #     "🏹 Точность",    2
        #     "❌ Миссы",       3
        #     "🔗 Комбо"        4
        #
        match_goal = match_entry.get('config', {}).get('goal')
        if match_goal is None:
            list.append('Цель раунда не настроена')
            raise CancelTryFinish(list, True, False)
        if match_goal == 0:     greater_wins = True
        elif match_goal == 1:   greater_wins = True
        elif match_goal == 2:   greater_wins = True
        elif match_goal == 3:   greater_wins = False
        elif match_goal == 4:   greater_wins = True
        else:
            list.append('Цель раунда не настроена')
            raise CancelTryFinish(list, True, False)
        
        def register_win(ending: str):

            match_entry['state']['winner'] = ending

            if ending == 'creator':
                list.append('Создатель выигрывает')                
            elif ending == 'member':
                list.append('Участник выигрывает')
            else: # ending == 'draw':
                list.append('Ничья')
            
            raise CancelTryFinish(list, True, True)

        if creator_result > member_result:
            if greater_wins:
                register_win('creator')
            else:
                register_win('member')
            
        elif creator_result < member_result:
            if greater_wins:
                register_win('member')
            else:
                register_win('creator')
            
        else:           
            register_win('draw')
            
    
    except CancelTryFinish as c:
        if c.list:
            if c.forward_list_back:
                return list, c.finished
            else:
                return [], c.finished
        else:
            print(f'[try_finish] CancelTryFinish without description')
            return [], False
    except Exception as e:
        print(e)
        return [], False
    
def process_elo(match_entry: dict | None = None):    
    # таймер должен быть проверен заранее
    # match_entry должен быть проверен
    try:
        # стейт раунда
        match_state = match_entry.get('state')
        if not match_state['elo_calculated']:
            
            # хз получить elo двух игроков 
            # допустим 1250 и 1014
            
            creator_elo = 1250 
            member_elo = 1014
            
            ending = match_entry['state']['winner']
            if ending == 'creator':
                creator_result = 1.0
            elif ending == 'member':
                creator_result = 0.0
            else: # ending == 'draw':
                creator_result = 0.5

            creator_elo_new, member_elo_new = update_elo(creator_elo, member_elo, creator_result)

            creator_delta = creator_elo_new - creator_elo
            member_delta = member_elo_new - member_elo

            return {
                "creator_elo_new": creator_elo_new,
                "member_elo_new": member_elo_new,
                "creator_delta": creator_delta,
                "member_delta": member_delta
            }        
        else: 
            raise ValueError('elo was already calculated for that match')
    except Exception as e:
        print(e)        
        return None


def calculate_expected(rating_a, rating_b):
    """
    Рассчитывает ожидаемый результат (вероятность победы) для игрока A.

    Args:
        rating_a (float): рейтинг игрока A
        rating_b (float): рейтинг игрока B

    Returns:
        float: вероятность победы игрока A (от 0 до 1)
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(rating_a, rating_b, result_a, k_factor=20):
    """
    Обновляет рейтинги двух игроков после матча.

    Args:
        rating_a (float): текущий рейтинг игрока A
        rating_b (float): текущий рейтинг игрока B
        result_a (float): результат матча для игрока A:
                         1 — победа, 0.5 — ничья, 0 — поражение
        k_factor (int): K‑фактор (коэффициент развития)

    Returns:
        tuple: (новый рейтинг игрока A, новый рейтинг игрока B)
    """
    expected_a = calculate_expected(rating_a, rating_b)
    expected_b = 1 - expected_a

    new_rating_a = rating_a + k_factor * (result_a - expected_a)
    new_rating_b = rating_b + k_factor * ((1 - result_a) - expected_b)

    return round(new_rating_a), round(new_rating_b)

# match = {
#     "started_at": "2026-05-20T09:04:08.982298+00:00",   # НОВОЕ ПОЛЕ
#     "track": True,      # трекинг этого раунда (отвечать ли сообщением)
#     "submit_state": {                                             
#       "creator": True,
#       "member": False,
#     },
#     "submit_result": {                                             
#       "creator": 20.0, 
#       "member": 31.0
#     },                                              # НОВОЕ ПОЛЕ

#     "config": {
#       "crossclient": 1,
#       "goal": 3,
#       "mods": [],
#       "source": 1,
#       "time": 4
#     },
#     "created_at": 1778930985,    
#     "member": {
#       "osu_id": 11596989,
#       "osu_name": "Fujiya",
#       "tg_id": 1803166423,
#       "tg_name": "fujiya_sama"
#     },
#     "id": "115969891778930985",
#     "intake": {
#       "map_full": "Oratorio The World God Only Knows - God only knows -Secrets of the Goddess- [The World Guy Only Knows]",
#       "map_id": "5274323",
#       "sent_id": 4287518921,
#       "sent_mods": "DT+DA",
#       "DA_values": {                # НОВОЕ ПОЛЕ
#         "circle_size": 3,
#         "approach_rate": 8.7, 
#       },
#       "sent_type": "score",
#       "temp_rank": "1"
#     },
#     "creator": {
#       "osu_id": 26197609,
#       "osu_name": "foundbpm",
#       "tg_id": 7354740126,
#       "tg_name": "foundbpm"
#     },
#     "pending_joins": [],
#     "state": {
#       "finished": False,
#       "started": True,
#       "winner": None,
#       "elo_calculated": False        # НОВОЕ ПОЛЕ
#     }
# }
# cached_entry = None
# try: cached_entry = load_score_file('6711851789')
# except: pass

# maybe_text = submit(cached_entry, match)
# if maybe_text is not None:
#     print(maybe_text)