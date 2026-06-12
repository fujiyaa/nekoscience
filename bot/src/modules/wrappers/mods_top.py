


from collections import Counter

from .userlink_rich import get_rich_userlink
from ..utils.osu_conversions import format_mods



def get_mods_top(user_data, scores):

    if not isinstance(scores, list) or not scores:
        return None

    mod_counter = Counter()
    combo_counter = Counter()
    combo_pp_weighted_sum = Counter()

    for score in scores:
        mods = score.get("mods", [])
        combo = format_mods(mods)

        if mods:
            for m in mods:
                mod_counter[m] += 1
        else:
            mod_counter["NM"] += 1

        combo_counter[combo] += 1

        pp = score.get("pp", 0.0) or 0.0
        weight = score.get("weight_percent", 0.0) or 0.0

        combo_pp_weighted_sum[combo] += pp * (weight / 100)

    total = len(scores)

    mod_table = pair_table(mod_counter, total, True, "Мод", "%")
    combo_table = pair_table(combo_counter, total, True, "Комбинация", "%")
    profit_table = pair_table(combo_pp_weighted_sum, None, False, "Комбинация", "PP")

    return f"""
{get_rich_userlink(user_data)}

<details open><summary>⦿ Любимые моды в топ100</summary>
{mod_table}
</details>
<details><summary>🔀 Любимые комбинации</summary>
{combo_table}
</details>
<details><summary>💰 Профит комбинации (pp)</summary>
{profit_table}
</details>"""
    
def pair_table(counter, total=None, is_percent=True, title_left="Mod", title_right="Usage"):
    items = list(counter.most_common())

    mid = (len(items) + 1) // 2
    left_col = items[:mid]
    right_col = items[mid:]

    def fmt(item):
        key, val = item

        if is_percent:
            val = (val / total * 100) if total else 0
            return f"{key} {val:.1f}%"
        else:
            return f"{key} {float(val):.1f}"

    def split(cell):
        parts = cell.rsplit(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return cell, "-"

    rows = []

    for i in range(len(left_col)):
        left = fmt(left_col[i])
        right = fmt(right_col[i]) if i < len(right_col) else "-"

        l_mod, l_val = split(left)
        r_mod, r_val = split(right)

        rows.append(f"| {l_mod} | {l_val} | {r_mod} | {r_val} |")

    return "\n".join([
        f"| {title_left} | {title_right} | {title_left} | {title_right} |",
        "|:--|:-:|:--|:-:|",
        *rows
    ])