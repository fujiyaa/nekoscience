


from decimal import Decimal
import re

def format_mods(mod_list):
    return "".join(mod_list) if mod_list else "NM"

def apply_mods_to_stats(bpm, ar, od, cs, hp, speed_multiplier=1.0, hr=False, ez=False):
    bpm = Decimal(str(bpm))
    ar = Decimal(str(ar))
    od = Decimal(str(od))
    cs = Decimal(str(cs))
    hp = Decimal(str(hp))
    speed_multiplier = Decimal(str(speed_multiplier))

    if ez:
        ar *= Decimal('0.5')
        od *= Decimal('0.5')
        cs *= Decimal('0.5')
        hp *= Decimal('0.5')      

    if hr:
        ar = min(ar * Decimal('1.4'), Decimal('10'))
        od = min(od * Decimal('1.4'), Decimal('10'))
        cs = min(cs * Decimal('1.3'), Decimal('10'))
        hp = min(hp * Decimal('1.4'), Decimal('10'))

    if speed_multiplier != 1:
        if ar < 5:
            ar_ms = Decimal('1800') - Decimal('120') * ar
        else:
            ar_ms = Decimal('1200') - Decimal('150') * (ar - 5)
        ar_ms /= speed_multiplier
        if ar_ms > 1200:
            ar = (Decimal('1800') - ar_ms) / Decimal('120')
        else:
            ar = Decimal('5') + (Decimal('1200') - ar_ms) / Decimal('150')

        hit300 = Decimal('80') - Decimal('6') * od
        hit100 = Decimal('140') - Decimal('8') * od
        hit50  = Decimal('200') - Decimal('10') * od

        hit300 /= speed_multiplier
        hit100  /= speed_multiplier
        hit50   /= speed_multiplier

        od = (Decimal('80') - hit300) / Decimal('6')

        bpm *= speed_multiplier

    def osu_round(val):
        return float(val.quantize(Decimal('0.01'), rounding='ROUND_HALF_UP'))

    bpm_r = osu_round(bpm)
    ar_r  = osu_round(ar)
    od_r  = osu_round(od)
    cs_r  = osu_round(cs)
    hp_r  = osu_round(hp)

    return bpm_r, ar_r, od_r, cs_r, hp_r

def get_mods_info(mods):
    mods_acronyms = []
    speed_multiplier = 1.0
    hr = False
    ez = False

    if mods:
        if isinstance(mods, str):
            mods_acronyms = mods.upper().split('+')
        elif isinstance(mods, list):
            mods_acronyms = [
                m['acronym'].upper() if isinstance(m, dict) else str(m).upper() 
                for m in mods
            ]

    hr = "HR" in mods_acronyms
    ez = "EZ" in mods_acronyms

    for mod in mods_acronyms:
        #"(X.XXX)"
        match = re.search(r'\(([\d.]+)X\)', mod)
        if match:
            try:
                speed_multiplier = float(match.group(1))
            except ValueError:
                pass
        else:
            if "DT" in mod or "NC" in mod:
                speed_multiplier = 1.5
            elif "HT" in mod:
                speed_multiplier = 0.75

    return speed_multiplier, hr, ez

def calculate_weighted_pp(best_pp, bonus_pp:float = 413.89):
    total_pp = 0.0
    for entry in best_pp:
        pp = float(entry['pp'])
        weight = entry.get('weight_percent', 100) / 100
        total_pp += pp * weight
    return (total_pp+bonus_pp)

def is_legacy_score(score: dict) -> bool:
    score_id = score.get("score_id")
    legacy_score_id = score.get("legacy_score_id")
    score_val = score.get("score")

    if not score_id or score_id == 0:
        if legacy_score_id or score_val:
            return True
        
    if legacy_score_id is not None:
        return True
    return False



# возможно не сюда

def insert_pp(data, new_pp, new_mods=None, new_mapper=''):
    if new_mods is None:
        new_mods = []

    saved_weights = [entry.get('weight_percent') for entry in data]

    if float(new_pp) < float(data[-1]['pp']):
        return None

    position = 0
    while position < len(data) and float(new_pp) < float(data[position]['pp']):
        position += 1

    new_entry = {
        'pp': float(new_pp),
        'mods': new_mods,
        'mapper': new_mapper
    }
    data.insert(position, new_entry)

    if len(data) > 100:
        data = data[:100]

    for i, weight in enumerate(saved_weights[:len(data)]):
        data[i]['weight_percent'] = weight

    return position, data