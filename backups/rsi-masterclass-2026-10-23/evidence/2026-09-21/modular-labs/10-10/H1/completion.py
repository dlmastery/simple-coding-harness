def check(record):
    if not record.get("candidate"):
        raise ValueError("missing candidate identity")
    if "duration_seconds" in record:
        return float(record["duration_seconds"])
    unit = record.get("duration_unit")
    if unit not in ("seconds", "minutes"):
        raise ValueError("missing or unsupported duration_unit")
    return float(record["duration_value"]) * (60 if unit == "minutes" else 1)
