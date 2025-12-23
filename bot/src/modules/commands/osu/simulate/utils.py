


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
        sess["params"][k] = str(values[k])
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
    elif accuracy > 95:
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

    text = "```\n"

    text += f"{'Ранк':<18}{'Точность':<12}\n"

    grade = sess["grade"]
    grade_text = grade + f' +{sess["params"].get("Моды")}'
    acc = sess["params"].get("Точность", "?")
    acc_text = f'{float(acc):.2f}% (CL)'
    combo = sess["params"].get("Комбо", max_combo)
    combo_text = f'{combo}x/{max_combo}x'

    text += f"{grade_text:<18}{acc_text:<12}\n\n"

    text += f"{'PP':<18}{'Hits':<12}\n"

    pp =  f"{pp:.1f}" if pp is not None else '?'
    pp_text = f"{pp}/{max_pp:.1f}PP"
    hits_text = "{"
    hits_text += f"{n300}/{n100}/{n50}/{expected_miss}"
    hits_text += "}"
    
    text += f"{pp_text:<18}{hits_text:<12}\n\n"

    aim, acc, speed = sess["aim"], sess["acc"], sess["speed"]
    skills_text = f"Aim:Acc:Speed"
    rate = f'{sess["params"].get("Скорость")}x'

    text += f"{skills_text:<22}{'Скорость':<8}\n"

    skills_text = f"{aim:.0f} : {acc:.0f} : {speed:.0f}"    
    text += f"{skills_text:<22}{rate:<8}\n"

    text += f""
    text += "```\n"

    return text
