


from ..systems.translations import DEFAULT_SCORES_PROP as SP



def get_average_table(table_data, lang, split_index=None):
    formatted_table_data = {}

    for key, values in table_data.items():
        formatted_values = []

        for v in values:     
            if isinstance(v, str):
                formatted_values.append(v)            
            elif isinstance(v, float):
                formatted_values.append(f"{v:.2f}")
            else:
                formatted_values.append(str(v))

        formatted_table_data[key] = formatted_values

    headers = [
        SP.get('Minimum')[lang],
        SP.get('Average')[lang],
        SP.get('Maximum')[lang]
    ]

    items = list(formatted_table_data.items())

    if split_index is None:
        split_index = len(items)

    core_items = items[:split_index]
    stat_items = items[split_index:]

    def build_table(rows_items, floating_header=False):
        if not rows_items:
            return ""

        rows = [[key, *values] for key, values in rows_items]

        header = f"| | {headers[0]} | {headers[1]} | {headers[2]} |"
        align = "|:--|:-:|:-:|:-:|"

        lines = []

        if floating_header:
            # первая строка как “разделитель секции”
            first = rows[0]
            lines.append(f"| {first[0]} | {first[1]} | {first[2]} | {first[3]} |")
            lines.append(align)
            rows = rows[1:]
        else:
            lines.append(header)
            lines.append(align)

        for row in rows:
            lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

        return "\n".join(lines)

    core_table = build_table(core_items)
    stat_table = build_table(stat_items, floating_header=True)

    return core_table, stat_table