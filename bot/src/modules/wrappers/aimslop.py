    


from ..utils.text_format import country_code_to_flag

from config import AIMSLOP_IDS



def get_aimslop_text(user_data, best_pp):
    
    if isinstance(best_pp, list) and best_pp:
              
        total = len(best_pp)
        counter = 0
        total_weighted_pp = 0
        aimslop_weighted_pp = 0

        for score in best_pp:
            beatmap_id = score.get("beatmap_id")
            pp = float(score.get("pp", 0))
            weight_percent = float(score.get("weight_percent", 0))

            weighted_pp = pp * (weight_percent / 100)
            total_weighted_pp += weighted_pp

            if beatmap_id and beatmap_id in AIMSLOP_IDS:
                counter += 1
                aimslop_weighted_pp += weighted_pp

        aimslop_percent = (counter / total) * 100 if total else 0

        aimslop_weighted_percent = (
            (aimslop_weighted_pp / total_weighted_pp) * 100
            if total_weighted_pp else 0
        )

        def percent_emoji(p):
            if p < 1:
                return '✅'
            elif p < 15:
                return '🟢'
            elif p < 30:
                return '🟡'
            elif p < 50:
                return '🟠'
            elif p < 70:
                return '❗️'
            else:
                return '‼️'

        row1_emoji = percent_emoji(aimslop_percent)
        row2_emoji = percent_emoji(aimslop_weighted_percent)

        col1_header = "Аимслоп в топ 100"
        col2_header = "N"
        col3_header = "%"
        col4_header = "чек"

        row1_label = "всего карт"
        row1_n = f"{counter}/{total}"
        row1_p = f"{aimslop_percent:.0f}%"

        row2_label = "pp слопа"
        row2_n = f"{aimslop_weighted_pp:.0f}pp"
        row2_p = f"{aimslop_weighted_percent:.0f}%"

        col1_width = max(len(col1_header), len(row1_label), len(row2_label))
        col2_width = max(len(col2_header), len(row1_n), len(row2_n))
        col3_width = max(len(col3_header), len(row1_p), len(row2_p))
        col4_width = max(len(col4_header), len(row1_emoji), len(row2_emoji))

        header = (
            f"{col1_header:<{col1_width}} | "
            f"{col2_header:^{col2_width}} | "
            f"{col3_header:^{col3_width}} | "
            f"{col4_header:^{col4_width}}"
        )

        separator = (
            f"{'-'*col1_width}-+-"
            f"{'-'*col2_width}-+-"
            f"{'-'*col3_width}-+-"
            f"{'-'*col4_width}"
        )

        row1 = (
            f"{row1_label:<{col1_width}} | "
            f"{row1_n:>{col2_width}} | "
            f"{row1_p:>{col3_width}} | "
            f"{row1_emoji:^{col4_width}}"
        )

        row2 = (
            f"{row2_label:<{col1_width}} | "
            f"{row2_n:>{col2_width}} | "
            f"{row2_p:>{col3_width}} | "
            f"{row2_emoji:^{col4_width}}"
        )

        table_text = "\n".join([header, separator, row1, row2])

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

        return f"{user_link}\n\n<pre>{table_text}</pre>"