


from .userlink_rich import get_rich_userlink



# для топчата
def get_nish_total(best_pp):

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

    return total_niche


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

    nish_rank = f"<i>Результат:</i>\n<code>{niche_title(niche_pp_percent, avg_map_niche, total_niche)}</code>"

    return f"""
{get_rich_userlink(user_data)}

| Нишевость | % | ✓ |
|:--|--:|:-:|
| нишевых РР | {niche_weighted_pp:.0f}pp | {row1_emoji} |
| средняя нишевость | {avg_map_niche/100:.2f} | {row2_emoji} |
| итого нишевости | {total_niche:.1f} | {row3_emoji} |

<details><summary>{nish_rank}</summary>

### мяу... как эта штука вообще работает? (=ω=)

ну смотри!!

я залезла в твой топ-100 и начала проверять, насколько странные карты ты себе понабивал... потому что некоторые люди играют обычный фарм, а некоторые находят карту, которую последний раз открывали ещё при динозаврах... >_<

---

### 🍞 шаг 1. насколько карта "подвальная"

у каждой карты есть примерное количество прохождений.

* если карту почти никто не трогал, то она получает **максимум нишевости!!**
* если её играли вообще все кому не лень, то она считается обычной метовой картой и почти ничего не даёт.

короче...

> меньше людей играло → больше ниша ↑

---

### 💸 шаг 2. сколько PP эта ниша реально приносит

потом я смотрю не просто на карты...

а на **PP**, который ты с них получил.

если твой топ держится на странных картах, которые никто не знает...

то показатель начинает довольно мурлыкать.

если же почти весь PP приехал с очередных Sotarks, Reform, Log Off Now и прочих жителей первой страницы osu!direct...

ну... мяу...

---

### 📚 шаг 3. средняя странность топа

дальше считается просто средняя нишевость всех карт.

без разницы, сколько PP они дают.

это уже показывает не силу профиля, а насколько ты вообще любишь копаться в архивах вместо того, чтобы жать Install на очередной Recommended Difficulty.

---

### 🧪 шаг 4. итог

в конце я смешиваю:

* сколько PP построено на нишевых картах;
* насколько нишевые сами карты.

и получается общий показатель.

поэтому невозможно стать великим нишевиком, случайно поставив одну древнюю карту на 17pp.

и невозможно выглядеть метовым только потому, что несколько популярных карт попали в топ.

---

### 🏷 а титул??

он собирается из **трёх кусочков**, как конструктор.

**первая часть** показывает, насколько нишевый твой PP.

**вторая** говорит, насколько странный сам пул карт.

**третья** определяет итоговую сущность твоего профиля.

поэтому можно получить что-нибудь вроде...

> 📚 Библиотечный глубинно нишевый архивист

или

> ⚡ Эффективный поверхностный юзер

или вообще

> 🕳 ... аномально нишевый шина

да... последнее тоже существует.

не спрашивай.

---

### ⚠️ важное мяу

нишометр **не измеряет скилл**.

он вообще не говорит, хороший ты игрок или нет.

он просто отвечает на очень важный вопрос человечества:

> **"ты фармила... или ты опять откопал карту с 14 фаворитами и 300к плейкаунта?"**

и да...

если итог получился очень высоким...

поздравляю.

ты официально живёшь где-то глубоко в osu!forums и, вероятно, знаешь больше никнеймов забытых мапперов, чем имён собственных родственников. =＾● ⋏ ●＾=

(помогите)
</details>
"""

