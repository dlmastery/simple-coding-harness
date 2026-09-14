"""Step 02 - a text renderer for an MCP App's structuredContent.

A terminal host cannot mount HTML. It can still show the data the view
would have drawn: the tool result's structuredContent. This module turns
any JSON value into lines of text. A list of flat dicts with the same keys
becomes a table; a dict becomes key: value lines; lists and scalars print
as they are. Nothing here knows about lemonade.
"""

import re

MAX_ROWS = 40


def lines(value, indent=0):
    """The value as a list of text lines."""
    pad = "  " * indent
    if is_table(value):
        return [pad + row for row in table(value)]
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                out.append(f"{pad}{key}:")
                out.extend(lines(item, indent + 1))
            else:
                out.append(f"{pad}{key}: {scalar(item)}")
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, (dict, list)):
                out.extend(lines(item, indent + 1))
            else:
                out.append(f"{pad}- {scalar(item)}")
        return out
    return [pad + scalar(value)]


def is_table(value):
    """A non-empty list of dicts that share their keys, with no nested values."""
    if not isinstance(value, list) or not value or not all(isinstance(row, dict) for row in value):
        return False
    keys = list(value[0].keys())
    return all(list(row.keys()) == keys for row in value) and not any(
        isinstance(cell, (dict, list)) for row in value for cell in row.values()
    )


def table(rows):
    """Rows as a padded text table with a header and a rule."""
    keys = list(rows[0].keys())
    cells = [[scalar(row[key]) for key in keys] for row in rows[:MAX_ROWS]]
    widths = [max(len(key), *(len(row[i]) for row in cells)) for i, key in enumerate(keys)]
    numeric = [all(is_number(row[i]) for row in cells) for i in range(len(keys))]

    def fmt(row):
        return "  ".join(cell.rjust(widths[i]) if numeric[i] else cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip()

    out = [fmt(keys), "  ".join("-" * width for width in widths)] + [fmt(row) for row in cells]
    if len(rows) > MAX_ROWS:
        out.append(f"... {len(rows) - MAX_ROWS} more rows")
    return out


def scalar(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def is_number(text):
    return re.fullmatch(r"-?\d+(\.\d+)?", text) is not None


def title_of(html):
    """The <title> of an HTML document, or None."""
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None
