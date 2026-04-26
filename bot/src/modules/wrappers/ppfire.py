def get_fire_text(
    period_text,
    days,
    total_scores,
    filtered_scores,
    raw_pp,
    weighted_pp,
    user_total_pp
):
    if total_scores is None:
        total_scores = 0

    # =========================
    # активность
    # =========================
    active_count = len(filtered_scores)
    active_per_day = active_count / days if days else 0

    active_percent = (active_per_day / 1.0) * 100
    weighted_percent = (weighted_pp / user_total_pp) * 100 if user_total_pp else 0
    raw_percent = (raw_pp / weighted_pp) * 100 if weighted_pp else 0

    # =========================
    # эмодзи активности
    # =========================
    def activity_emoji(p):
        if p < 2:
            return "💀"
        if p < 4:
            return "❗️"
        elif p < 8:
            return "🔴"
        elif p < 16:
            return "🟠"
        elif p < 20:
            return "🟡"
        else:
            return "🟢"

    def contribution_emoji(p):
        if p < 2:
            return "💀"
        if p < 4:
            return "❗️"
        elif p < 8:
            return "🔴"
        elif p < 16:
            return "🟠"
        elif p < 20:
            return "🟡"
        else:
            return "🟢"

    def overflow_emoji(p):
        if p < 120:
            return "❗️"
        elif p < 140:
            return "🔴"
        elif p < 160:
            return "🟠"
        elif p < 180:
            return "🟡"
        else:
            return "🟢"

    headers = [f"Костёр ({period_text})", "N", "%", "чек"]

    rows = [
        (
            "новых скоров/день",
            f"{active_count}/{days}",
            f"{active_percent:.0f}%",
            activity_emoji(active_percent)
        ),
        (
            "взвешено",
            f"{weighted_pp:.0f}pp",
            f"{weighted_percent:.0f}%",
            contribution_emoji(weighted_percent)
        ),
        (
            "overflow",
            f"{raw_pp:.0f}pp",
            f"{raw_percent:.0f}%",
            overflow_emoji(raw_percent)
        ),
    ]

    col1 = max(len(headers[0]), *(len(r[0]) for r in rows))
    col2 = max(len(headers[1]), *(len(r[1]) for r in rows))
    col3 = max(len(headers[2]), *(len(r[2]) for r in rows))
    col4 = max(len(headers[3]), *(len(r[3]) for r in rows))

    header = (
        f"{headers[0]:<{col1}} | "
        f"{headers[1]:^{col2}} | "
        f"{headers[2]:^{col3}} | "
        f"{headers[3]:^{col4}}"
    )

    sep = (
        f"{'-'*col1}-+-"
        f"{'-'*col2}-+-"
        f"{'-'*col3}-+-"
        f"{'-'*col4}"
    )

    body = "\n".join(
        f"{r[0]:<{col1}} | {r[1]:>{col2}} | {r[2]:>{col3}} | {r[3]:^{col4}}"
        for r in rows
    )

    return f"<pre>{header}\n{sep}\n{body}</pre>"