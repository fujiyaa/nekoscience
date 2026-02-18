    


from ..utils.text_format import country_code_to_flag



def get_anime_text(user_data, best_pp):
    
    if isinstance(best_pp, list) and best_pp:
              
        total = len(best_pp)
        anime_bg_counter, not_anime_bg_counter = 0, 0

        for score in best_pp:
            if score.get("is_anime_bg", False):
                anime_bg_counter += 1
            else:
                not_anime_bg_counter += 1

        anime_percent = (anime_bg_counter / total) * 100 if total else 0
        other_percent = (not_anime_bg_counter / total) * 100 if total else 0

        entry_width = len("Anime backgrounds")
        count_width = len("100.0%")

        table_lines = [
            f"{'Anime backgrounds':<{entry_width}} | {'top100':>{count_width}}",
            f"{'-'*entry_width}-+-{'-'*count_width}",
            f"{'anime':<{entry_width}} | {anime_percent:>{count_width}.0f}%",
            f"{'other':<{entry_width}} | {other_percent:>{count_width}.0f}%"
        ]

        table_text = "\n".join(table_lines)

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
