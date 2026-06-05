from ..utils.text_format import country_code_to_flag


def get_nish_text(user_data, best_pp):

    if not (isinstance(best_pp, list) and best_pp):
        return None

    def niche_score(playcount, low=450_000, high=550_000):

        if not playcount:
            return 1.0

        if playcount <= low:
            return 1.0

        if playcount >= high:
            return 0.0
        
        return 1 - ((playcount - low) / (high - low))

    def percent_emoji(p):
        if p < 1:
            return "🧼"
        elif p < 5:
            return "✅"
        elif p < 10:
            return "🟢"
        elif p < 15:
            return "🟩"
        elif p < 20:
            return "🟡"
        elif p < 25:
            return "🟨"
        elif p < 30:
            return "🟠"
        elif p < 40:
            return "🟧"
        elif p < 50:
            return "⚠️"
        elif p < 60:
            return "❗️"
        elif p < 70:
            return "🚨"
        elif p < 80:
            return "☠️"
        elif p < 90:
            return "💀"
        elif p < 100:
            return "🧿"
        else:
            return "🕳"

    def niche_title(pp_n, avg_n, total_n):

        def invert(n):
            return max(0, 100 - n)

        def pp_part(n):

            if n < 8:
                return "📱 Метовый"
            elif n < 15:
                return "⚡ Эффективный"
            elif n < 22:
                return "🧠 Оптимизированный"
            elif n < 30:
                return "🧩 Нестандартный"
            elif n < 38:
                return "🕹 Тактический"
            elif n < 46:
                return "🕳 Массового поражения"
            elif n < 54:
                return "📚 Библиотечный"
            elif n < 62:
                return "🧪 Подземельный"
            elif n < 70:
                return "☠️ Загробный"
            elif n < 78:
                return "💀 Потусторонний"
            elif n < 86:
                return "🧿 Искажённый"
            elif n < 93:
                return "🕳 Анти-мета"
            else:
                return "🕳 ..."

        def avg_part(n):

            if n < 8:
                return "мейнстримный"
            elif n < 15:
                return "трендовый"
            elif n < 22:
                return "поверхностный"
            elif n < 30:
                return "не внимательный"
            elif n < 38:
                return "подозрительный"
            elif n < 46:
                return "странный"
            elif n < 54:
                return "сбалансированный"
            elif n < 62:
                return "нишевый"
            elif n < 70:
                return "архивно-нишевый"
            elif n < 78:
                return "крайне редко-нишевый"
            elif n < 86:
                return "глубинно нишевый"
            else:
                return "аномально нишевый"

        def entity_part(n):

            if n < 8:
                return "лютый фармила"
            elif n < 15:
                return "дефолтный фармила"
            elif n < 22:
                return "юзер"
            elif n < 30:
                return "копатель"
            elif n < 38:
                return "улучшенный копатель"
            elif n < 46:
                return "черный копатель"
            elif n < 54:
                return "последний копатель"
            elif n < 62:
                return "архивист"
            elif n < 70:
                return "коллекционер"
            elif n < 78:
                return "нишевик"
            elif n < 86:
                return "аномалия"
            elif n < 93:
                return "сущность"
            else:
                return "шина"
            
        return f"{pp_part(pp_n)} {avg_part(avg_n)} {entity_part(total_n)}"


    total = len(best_pp)

    niche_weighted_pp = 0.0
    total_weighted_pp = 0.0
    niche_sum = 0.0

    niche_cards_count = 0

    for score in best_pp:

        pp = float(score.get("pp", 0))
        weight_percent = float(score.get("weight_percent", 0))
        playcount = score.get("mapset_plays") or 0

        niche = niche_score(playcount)

        if niche > 0.5:
            niche_cards_count += 1

        weighted_pp = pp * (weight_percent / 100)

        total_weighted_pp += weighted_pp
        niche_weighted_pp += weighted_pp * niche
        niche_sum += niche

    # print(f"niche_cards_count = {niche_cards_count} / {total}")

    niche_pp_percent = (
        (niche_weighted_pp / total_weighted_pp) * 100
        if total_weighted_pp
        else 0
    )

    avg_map_niche = (
        (niche_sum / total) * 100
        if total
        else 0
    )

    total_niche = (niche_pp_percent + avg_map_niche) / 2

    row1_emoji = percent_emoji(niche_pp_percent)
    row2_emoji = percent_emoji(avg_map_niche)
    row3_emoji = percent_emoji(total_niche)

    col1_header = "Нишевость"
    col2_header = "N"
    col3_header = "чек"

    row1_label = "нишевых pp"
    row1_n = f"{niche_weighted_pp:.0f}pp"

    row2_label = "средняя нишевость"
    row2_n = f"{avg_map_niche/100:.2f}"

    row3_label = "всего нишевости"
    row3_n = f"{total_niche:.1f}"

    col1_width = max(
        len(col1_header),
        len(row1_label),
        len(row2_label),
        len(row3_label),
    )

    col2_width = max(
        len(col2_header),
        len(row1_n),
        len(row2_n),
        len(row3_n),
    )

    col3_width = max(
        len(col3_header),
        len(row1_emoji),
        len(row2_emoji),
        len(row3_emoji),
    )

    header = (
        f"{col1_header:<{col1_width}} | "
        f"{col2_header:^{col2_width}} | "
        f"{col3_header:^{col3_width}}"
    )

    separator = (
        f"{'-'*col1_width}-+-"
        f"{'-'*col2_width}-+-"
        f"{'-'*col3_width}"
    )

    row1 = (
        f"{row1_label:<{col1_width}} | "
        f"{row1_n:<{col2_width}} | "
        f"{row1_emoji:^{col3_width}}"
    )

    row2 = (
        f"{row2_label:<{col1_width}} | "
        f"{row2_n:<{col2_width}} | "
        f"{row2_emoji:^{col3_width}}"
    )

    final_separator = separator

    row3 = (
        f"{row3_label:<{col1_width}} | "
        f"{row3_n:<{col2_width}} | "
        f"{row3_emoji:^{col3_width}}"
    )

    table_text = "\n".join([
        header,
        separator,
        row1,
        row2,
        final_separator,
        row3,
    ])

    username = user_data["username"]
    stats = user_data["statistics"]

    pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"

    global_rank_text = (
        f"(#{stats.get('global_rank'):,}"
        if stats.get("global_rank")
        else "(#????"
    )

    country_rank_text = (
        f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
        if stats.get("country_rank")
        else f"  {user_data['country_code']}#???)"
    )

    rank_text = (
        f"{username}: "
        f"{pp_text}pp "
        f"{global_rank_text}"
        f"{country_rank_text}"
    )

    country_flag = country_code_to_flag(user_data["country_code"])

    user_id = f"https://osu.ppy.sh/users/{user_data['id']}"

    user_link = (
        f'<a href="{user_id}">'
        f'{country_flag} <b>{rank_text}</b>'
        f"</a>"
    )

    niche_rank = f"<i>Результат:</i>\n<code>{niche_title(niche_pp_percent, avg_map_niche, total_niche)}</code>"

    return (
        f"{user_link}\n\n"
        f"<pre>{table_text}</pre>\n\n"
        f"{niche_rank}"
    )