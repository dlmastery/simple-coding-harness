"""Step 01 - the lemonade stand's sales, deterministic so the tests are exact.

A tiny generator stands in for a database. The same `days` always gives the
same rows, so the tool result can be checked byte for byte.
"""

import random

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PRICE = 1.5  # dollars per cup


def sales(days: int, seed: int = 7) -> list[dict]:
    """One row per day: name, temperature, cups sold, revenue."""
    rng = random.Random(seed)
    rows = []
    for index in range(days):
        temperature = rng.randint(18, 34)
        cups = 10 + (temperature - 18) * 3 + rng.randint(-5, 5)
        rows.append({
            "day": DAY_NAMES[index % 7],
            "temperature": temperature,
            "cups": cups,
            "revenue": round(cups * PRICE, 2),
        })
    return rows


def summary(rows: list[dict]) -> dict:
    """The three numbers a metric card wants, plus the best day."""
    best = max(rows, key=lambda row: row["cups"])
    return {
        "total_cups": sum(row["cups"] for row in rows),
        "total_revenue": round(sum(row["revenue"] for row in rows), 2),
        "best_day": best["day"],
    }


def as_text(days: int, rows: list[dict]) -> str:
    """The plain-text version of the dashboard: what the model reads, what a text host shows."""
    totals = summary(rows)
    lines = [f"Lemonade stand, last {days} days: {totals['total_cups']} cups, ${totals['total_revenue']:.2f} revenue, best day {totals['best_day']}."]
    for row in rows:
        lines.append(f"{row['day']}: {row['cups']} cups at {row['temperature']} C (${row['revenue']:.2f})")
    return "\n".join(lines)
