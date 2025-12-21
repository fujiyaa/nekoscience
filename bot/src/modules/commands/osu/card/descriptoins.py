


from collections import Counter



def get_prefix(value: float) -> str:
    if value < 10: return "Newbie"
    if value < 20: return "Novice"
    if value < 30: return "Rookie"
    if value < 40: return "Apprentice"
    if value < 50: return "Advanced"
    if value < 60: return "Outstanding"
    if value < 70: return "Seasoned"
    if value < 80: return "Professional"
    if value < 85: return "Expert"
    if value < 90: return "Master"
    if value < 95: return "Legendary"
    return "God"

def get_suffix(aim: float, speed: float, acc: float, tol: float = 3.0) -> str:   
    if abs(aim - speed) < tol and abs(speed - acc) < tol:
        return "All-Rounder"
    if acc > aim and acc > speed and abs(aim - speed) < tol:
        return "Rhythm Enjoyer"
    if aim > acc and aim > speed and abs(acc - speed) < tol:
        return "Whack-A-Mole"
    if speed > aim and speed > acc and abs(aim - acc) < tol:
        return "Masher"
    if acc > speed and aim > speed:
        return "Sniper"
    if acc > aim and speed > aim:
        return "Ninja"
    if aim > acc and speed > acc:
        return "Gunslinger"
    return "Undefined"

def get_title(aim: float, speed: float, acc: float, scores) -> str:
    max_skill = max(aim, speed, acc)
    prefix = get_prefix(max_skill)

    description = get_description(scores, mode="osu")

    suffix = get_suffix(aim, speed, acc, 10) # для 100 скоров = 3

    return prefix, f"{prefix} {description} {suffix}"

def get_description(scores: dict, mode) -> str:
    mods_counter = Counter()
    total = len(scores) or 1

    for score in scores:
        mods = score.mods or ["NM"]
        for m in mods:
            mods_counter[m] += 1

    def percent(mod: str) -> float:
        return mods_counter[mod] * 100 / total

    if percent("NM") > 70:
        return "Mod-Hating"
    
    bonus_title = ""
    if mode == "osu":
        if percent("HD") > 60:
            bonus_title = "HD-Abusing"
        if percent("HR") > 60:
            bonus_title = "Ant-Clicking"
        if percent("EZ") > 15:
            bonus_title = "Patient"
    
    # if percent("HD") > 60:
    #     return random.choice(["HD-Abusing", "Ghost-Fruits", "Brain-Lag"])
    # if percent("HR") > 60:
    #     return random.choice(["Ant-Clicking", "Zooming", "Pea-Catching"])
    # if percent("EZ") > 15:
    #     return random.choice(["Patient", "Training-Wheels", "3-Life"])
        
    if percent("DT") + percent("NC") > 60:
        return f"Speedy {bonus_title}"
    if percent("HT") > 30:
        return f"Slow-Mo {bonus_title}"
    if percent("FL") > 15:
        return f"Blindsighted {bonus_title}"
    if percent("SO") > 20:
        return f"Lazy-Spin {bonus_title}"
    if percent("MR") > 30:
        return f"Unmindblockable {bonus_title}"

    if percent("NM") < 6: # изменить при другом количестве скоров!!!
        return "Mod-Loving"

    return "Versatile"
