


from ..systems.translations import DEFAULT_SCORES_PROP as SP



def get_minmax_table(table_data, lang, split_index=None):

    def format_value(value, score_id, formatter=None):
        if value == " " or score_id == " ":
            return " "

        if formatter:
            value_str = formatter(value)
        else:
            try:
                value_str = f"{float(value):.2f}"
            except (ValueError, TypeError):
                value_str = str(value)

        if score_id:
            return f"<a href='https://osu.ppy.sh/scores/{score_id}'>{value_str}</a>"

        return value_str

    formatters = {
        SP.get('Length')[lang]: format_time
    }

    items = list(table_data.items())

    if split_index is None:
        split_index = len(items)

    core_items = items[:split_index]
    stat_items = items[split_index:]

    headers = [
        SP.get('Minimum')[lang],
        SP.get('Maximum')[lang]
    ]

    def build_table(rows_items, floating_header=False):
        if not rows_items:
            return ""

        rows = []

        for key, values in rows_items:
            (min_v, min_id), (max_v, max_id) = values

            formatter = formatters.get(key)

            min_cell = format_value(min_v, min_id, formatter)
            max_cell = format_value(max_v, max_id, formatter)

            rows.append([key, min_cell, max_cell])

        lines = []

        align = "|:--|:-:|:-:|"

        if floating_header and rows:
            first = rows[0]
            lines.append(f"| {first[0]} | {first[1]} | {first[2]} |")
            lines.append(align)
            rows = rows[1:]
        else:
            lines.append(f"|  | {headers[0]} | {headers[1]} |")
            lines.append(align)

        for r in rows:
            lines.append(f"| {r[0]} | {r[1]} | {r[2]} |")

        return "\n".join(lines)

    core_table = build_table(core_items)
    stat_table = build_table(stat_items, floating_header=True)

    return core_table, stat_table
    
def format_time(seconds):
    if isinstance(seconds, str):
        return seconds
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
