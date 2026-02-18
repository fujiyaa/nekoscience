


from collections import Counter, defaultdict

from ..utils.text_format import format_blocks_percent, format_blocks_pp, country_code_to_flag
from ..utils.osu_conversions import format_mods



def get_mods_top(user_data, scores):   
    
    if isinstance(scores, list) and scores:
        mod_counter = Counter()
        combo_counter = Counter()
        # combo_pp_sum = defaultdict(float)
        combo_pp_weighted_sum = defaultdict(float)

        for score in scores:
            mods = score.get("mods", [])
            combo = format_mods(mods)

            if mods:
                for m in mods:
                    mod_counter[m] += 1
            else:
                mod_counter["NM"] += 1

            combo_counter[combo] += 1

            pp_value = score.get("pp", 0.0) or 0.0
            weight_percent = score.get("weight_percent", 0.0) or 0.0

            # combo_pp_sum[combo] += pp_value
            combo_pp_weighted_sum[combo] += pp_value * (weight_percent / 100)

        total_scores = len(scores)

        fav_mods_str = format_blocks_percent(mod_counter, total_scores, per_row=4)
        fav_combos_str = format_blocks_percent(combo_counter, total_scores, per_row=3)
        # profit_combos_str = format_blocks_pp(combo_pp_sum, per_row=3)
        weighted_combos_str = format_blocks_pp(combo_pp_weighted_sum, per_row=3)

        username = user_data["username"]                
        stats = user_data["statistics"]

        pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
        global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
        country_rank_text = (
            f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
            if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
        )

        rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
        country_flag = country_code_to_flag(user_data["country_code"])

        user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
        user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'                
        
        text = (
            f"{user_link}\n\n"
            "⦿ <b><u>Top100 mods:</u></b>\n\n"
            f"<b>Favourite mods</b>\n{fav_mods_str}\n\n"
            f"<b>Favourite mod combinations</b>\n{fav_combos_str}\n\n"
            # f"<b>Profitable mod combinations (pp)</b>\n{profit_combos_str}\n\n"
            f"<b>Profitable mod combinations (pp)</b>\n{weighted_combos_str}"
        )

        return text