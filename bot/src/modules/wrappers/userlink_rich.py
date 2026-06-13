    


from ..utils.text_format import country_code_to_flag



def get_rich_userlink(user_data):

    try:
        if isinstance(user_data, dict):
            username = user_data["username"]
            stats = user_data["statistics"]
            pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
            global_rank_text = f"#{stats.get('global_rank'):,}" if stats.get("global_rank") else "#????"
            country_rank_text = (
                f"{user_data['country_code']}#{stats.get('country_rank'):,}"
                if stats.get("country_rank") else f"{user_data['country_code']}#???"
            )
            rank_text = f"{username}: {pp_text}pp <sup>{global_rank_text} ({country_rank_text})</sup>"
            country_flag = country_code_to_flag(user_data["country_code"])

            user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
            user_link = f'<h3><a href="{user_id}">{country_flag} {rank_text}</a></h3>'

            return user_link
        else:
            raise ValueError
    except:
        return "profile link error 1"
