


from .....utils.text_format import seconds_to_hhmmss

from config import sessions_simulate



def calc_accuracy(n300, n100, n50, miss):
    total_hits = n300 + n100 + n50 + miss
    if total_hits == 0:
        return 0.0
    acc = (300 * n300 + 100 * n100 + 50 * n50) / (300 * total_hits)
    return acc * 100 
def update_hits(sess, param_name, new_value):
    priority = ["300", "100", "50", "мисс"]
    key_map = {"300k": "300", "100k": "100", "50k": "50", "miss": "мисс"}
    real_name = key_map.get(param_name, param_name)
    print("update_hits called with:", param_name, "->", key_map.get(param_name))
    
    changed_flags = {
        "300": sess["300_changed"],
        "100": sess["100_changed"],
        "50": sess["50_changed"],
        "мисс": sess["miss_changed"],
    }
    values = {k: int(sess["params"][k]) for k in priority}

    fixed = {k: v for k, v in values.items() if changed_flags[k] and v > 0}
    free = [k for k in priority if not changed_flags[k] or values[k] == 0]

    if len(fixed) >= 3 and not changed_flags[real_name]:
        return

    values[real_name] = int(new_value)
    if real_name == "300":
        sess["300_changed"] = new_value != 0
    elif real_name == "100":
        sess["100_changed"] = new_value != 0
    elif real_name == "50":
        sess["50_changed"] = new_value != 0
    elif real_name == "мисс":
        sess["miss_changed"] = new_value != 0

    changed_flags = {
        "300": sess["300_changed"],
        "100": sess["100_changed"],
        "50": sess["50_changed"],
        "мисс": sess["miss_changed"],
    }
    fixed = {k: v for k, v in values.items() if changed_flags[k] and v > 0}
    free = [k for k in priority if not changed_flags[k] or values[k] == 0]

    total = sess["max_hits"]
    sum_fixed = sum(fixed.values())
    remaining = max(0, total - sum_fixed)

    for k in priority:
        if k in free:
            values[k] = remaining
            break

    for k in priority:
        sess["params"][k] = values[k]

def calculate_rank(n300: int, n100: int, n50: int, miss: int, lazer: bool = True) -> str:
    n300 = int(n300 or 0)
    n100 = int(n100 or 0)
    n50 = int(n50 or 0)
    miss = int(miss or 0)
    total_hits = n300 + n100 + n50 + miss
    if total_hits == 0:
        return "D"

    if lazer:
        accuracy = (300*n300 + 100*n100 + 50*n50) / (300*total_hits) * 100
    else:
        accuracy = (n300 + n100*2/3 + n50*1/3) / total_hits * 100

    if miss == 0 and n300 == total_hits:
        rank = "SS"
    elif miss == 0 and accuracy > 95:
        rank = "S"
    elif accuracy > 90:
        rank = "A"
    elif accuracy > 80:
        rank = "B"
    elif accuracy > 70:
        rank = "C"
    else:
        rank = "D"

    return rank

def format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss):
    sess = sessions_simulate[user_id]
    schema = sess["schema"]

    grade = sess["grade"]
    grade_text = grade + f' +{sess["params"].get("Моды")}'
    acc = sess["params"].get("Точность", 100.0)
    acc_text = f'{float(acc):.2f}%'
    combo = sess["params"].get("Комбо", max_combo)
    combo_text = f'{combo}x/{max_combo}x'
  

    if int(pp) == int(max_pp):
        choke_title = choke_value = "<code>-</code>"
        
        pp_text_alt = f'<b>{pp:.2f}</b>'

    else:
        choke_title = 'Чоук'
        choke_value = pp - max_pp
        choke_value = f'{choke_value:.2f}'

        pp =  f"{pp:.1f}" if pp is not None else '?'
        pp_text_alt = f"{pp}/{max_pp:.1f}PP"
 
   
    aim_f = format_stat_2("aim", sess["aim"], sess["aim_u"])
    acc_f = format_stat_2("acc.", sess["acc"], sess["acc_u"])
    spd_f = format_stat_2("speed", sess["speed"], sess["speed_u"])

    rate = sess["params"].get("Скорость")

    if rate == 1.0:
        rate_text = ''
    else:
        rate_text = f' ({rate}x) '

    map_cs = schema['cs']['default']
    map_ar = schema['ar']['default']
    map_od = schema['od']['default']
    map_hp = schema['hp']['default']

    cs = format_stat("CS", map_cs, sess['params']['cs'])
    ar = format_stat("AR", map_ar, sess['params']['ar'])
    od = format_stat("OD", map_od, sess['params']['od'])
    hp = format_stat("HP", map_hp, sess['params']['hp'])

    map_url = sess['map_url']
    map_full = sess['beatmap_escaped']
    map_text = f'<a href="{map_url}">{map_full} [{stars:.2f}★]</a>'

    if sess['params']['Лазер']: 
        is_stable_client = ""
    else:
        is_stable_client = "(Stable)"

    caption = f"""   
##### {sess['username']}
{sess['cover_rich_block']}

<details><summary>{map_text}</summary>

| <code>Автор (сет)</code> | <a href="{map_url}">{sess['creator']}</a> 🔗 | <code>ID карты</code> | <code>{sess['beatmap']}</code> |
|:--:|:------------:|:--:|:------------:|
|{map_cs:g}<sub>CS</sub>|{map_ar:g}<sub>AR</sub>|{map_od:g}<sub>OD</sub>|{map_hp:g}<sub>HP</sub>|
| <code>Объекты</code> | {sess['max_hits']} | <code>Статус</code> | {sess['status']} |

</details>

<h3>{grade_text}{rate_text}{is_stable_client} 〰️ <code>Симуляция</code></h3>

|Точность*</code></sup>|{choke_title}|PP| 
|:-:|:-:|:-:|
|{acc_text}|{choke_value}|{pp_text_alt}|
|<code>{acc_f}</code>|<code>{aim_f}</code>|<code>{spd_f}</code>|

|{n300}<sub>300</sub>|{n100}<sub>100</sub>|{n50}<sub>50</sub>|{expected_miss}<sub>x</sub>|
|:-:|:-:|:-:|:-:|
|<code>{cs}</code>|<code>{ar}</code>|<code>{od}</code>|<code>{hp}</code>|
| <code>Длина</code> | {seconds_to_hhmmss(sess['hit_length_updated'])} | <code>BPM</code> | {expected_bpm:g} |
"""

    return caption

def format_stat(name, base, modified):
    if modified > base:
        icon = "🔺"
    elif modified < base:
        icon = "🔻"
    else:
        icon = ""

    return f"{icon}{modified:g}<sub>{name}</sub>"

def format_stat_2(name, base, modified):
    if modified > base:
        icon = "⭡"
    elif modified < base:
        icon = "⭣"
    else:
        icon = ""

    return f"{icon}{modified:.0f}<sub>{name}</sub>"

def truncate(text: str, length: int = 6):
    if len(text) <= length:
        return text
    return text[:length] + ".."
