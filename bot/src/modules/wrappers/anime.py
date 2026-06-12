    


from .userlink_rich import get_rich_userlink



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

        return f"""
{get_rich_userlink(user_data)}

| Аниме фоны в топ100 | % |
|:--|:-:|
| Да | {anime_percent:.0f}% |
| Нет | {other_percent:.0f}% |
"""