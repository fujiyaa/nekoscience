    


from .userlink_rich import get_rich_userlink

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
            elif p < 20:
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

        gwb_url = "https://docs.google.com/spreadsheets/d/1k-l8SVROL6bnL035mmBAOnTwLWxkw7GWUGDIEFHgXzE/edit?gid=1661256767#gid=1661256767"

        return f"""
{get_rich_userlink(user_data)}

| Аимслоп | N | % | ✓ |
|:--------|--:|--:|:-:|
| Карт в топ100 | <b>{counter}</b><code>/{total}</code> | {aimslop_percent:.0f}% | {row1_emoji} |
| PP аимслопа | <b>{aimslop_weighted_pp:.0f}</b>pp | {aimslop_weighted_percent:.0f}% | {row2_emoji} |

<details>
- <b>Карт в топ100</b> - количество из топ100 игрока, аимслоп определяется по <a href="{gwb_url}"><b>Таблице 🔗</b></a>
- <b>PP слопа</b> - сумма скоров, которые вошли в аимслоп список (сохраняется оригинальное взвешивание)
- Чем больше аимслопа тем хуже эмодзи.
</details>
"""