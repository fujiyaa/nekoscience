


from ..utils.text_format import country_code_to_flag



async def get_user_link(cached_entry: dict = None):
    user = cached_entry.get('user')
    user_id = cached_entry.get('osu_score', []).get("user_id")
    username = user.get("username")
    
    total_pp = user.get('total_pp', '0')
    global_rank = user.get('global_rank')
    country_rank = user.get('country_rank')
    country_code = user.get('country_code')

    country_flag = country_code_to_flag(country_code)

    country_rank_text = (
        f"  {country_code}#{country_rank:,})"
    )

    rank_text = (
        f"{username}: {total_pp}pp (#{global_rank}{country_rank_text}"
    )    

    return f'<a href="https://osu.ppy.sh/users/{user_id}">{country_flag} <b>{rank_text}</b></a>'