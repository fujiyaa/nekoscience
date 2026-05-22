


from datetime import datetime, timedelta, timezone

from ....external.localapi import read_file_neko, insert_to_file_neko
from .elo import process_elo
from .transaction import transaction
from .match import find_matches_by_user
from .utils import *
from .exceptions import *

from .options import d_file, m_file
TIME_OPTIONS = [1, 2, 3, 6, 12, 24, 48]
CROSSCLIENT_OPTIONS = ["🔹Лазер", "🔸Стейбл"]
GOAL_OPTIONS = [
    "🆕 SCORE-V2",
    "👨‍🦳 SCORE-STD",
    "🏹 Точность",
    "❌ Миссы",
    "🔗 Комбо"
]



async def submit(cached_entry: dict | None = None, match_entry: dict | None = None) -> str | None:    
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
        
        match_source = match_config.get('source')
        if match_source == 0:
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
            match_mods = match_config.get('mods')
            score_mods = score_mods

            normalized_match = normalize_mods(match_mods) or set()
            normalized_score = normalize_mods(score_mods) or set()

            if normalized_match != normalized_score:
                print('[submit] mods does not match')

                incorrections_list.append(
                    f'Моды: {"+".join(sorted(normalized_score))}, '
                    f'а нужно {"+".join(sorted(normalized_match))}'
                )
        
        # клиент: 0 - стейбл, 1 - лазер
        match_client = match_config.get('crossclient')
        if match_client is None:
            print(f'[submit] match_client is None')
            return
        score_client = cached_entry.get('state').get('lazer')
        if score_client is None:
            print(f'[submit] score_client is None')
            return
        if bool(score_client) == bool(match_client):
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
            score_goal_data = cached_entry.get('osu_score', {}).get('accuracy')*100
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

                users = [
                    creator_osu_id,
                    member_osu_id
                ]                

                response = await read_file_neko(d_file)
                data = response.get("current", {})

                for osu_id in users:
                    user = data.get(str(osu_id))

                    if not user:
                        print(f'[submit] user not found: {osu_id}') 
                        continue

                    user = data[str(osu_id)]
                    points = user.get("points")                    
              
                    if str(osu_id) == str(creator_osu_id):
                        creator_old_elo = points['current']  
                    else:
                        member_old_elo = points['current']

                print(f"{creator_old_elo}, {member_old_elo}")
                ratings = process_elo(creator_old_elo, member_old_elo, match_entry)

                for osu_id in users:
                    user = data.get(str(osu_id))

                    if not user:
                        print(f'[submit] user not found: {osu_id}') 
                        continue

                    user = data[str(osu_id)]
                    config = user.get("config")
                    intake = user.get("intake")
                    points = user.get("points")
                    active_matches = user.get("active_matches")
                    meta = user.get("meta")
                    current = points.get("current")
                    rank = intake.get("temp_rank")
                    osu, tg = user.get("osu"), user.get("telegram")     
                    osu_name, osu_id = osu.get("username"), osu.get("id")
                    tg_name, tg_id = tg.get("username"), tg.get("id")
                    map_full = intake['map_full']

                    response = await read_file_neko(m_file)
                    matches = response.get("current", {})
                    match = matches.get(match_entry['id'])
                    
              
                    if str(osu_id) == str(creator_osu_id):
                        new_elo = ratings['creator_elo_new']
                    else:
                        new_elo = ratings['member_elo_new']

                    points['current'] = new_elo

                    print(f'[submit] {osu_id} -> {new_elo}')

                await insert_to_file_neko(d_file, data)    




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

async def submit_all(cached_entry: dict | None = None) -> str | None:

    if not none_check(cached_entry, 'cached_entry'): return

    try:        
        user_id = cached_entry.get('osu_score', {}).get('user_id')
        
        if user_id is None: return

        user_id = str(user_id)

        async with transaction():

            matches = await find_matches_by_user(user_id)

            if matches is None:
                return
            
            if len(matches) < 1:
                return

            text_info = ""        
            for item in matches:
                text = await submit(cached_entry, item)
                if text is not None:
                    text_info += f"[{item['id'][-5:]}] "
                    text_info += text
                    text_info += "\n"

            if text_info == "": 
                return
            else:
                return text_info

    except Exception as e:
        print(e)
        pass