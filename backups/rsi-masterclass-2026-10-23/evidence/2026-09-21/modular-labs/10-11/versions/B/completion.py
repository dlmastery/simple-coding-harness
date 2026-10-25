def check(record):
    if not record.get("candidate"):
        raise ValueError("missing candidate identity")
    if "duration_unit" not in record:
        raise ValueError("required duration_unit absent at completion interface")
    unit = record["duration_unit"]
    if unit not in ("seconds", "minutes"):
        raise ValueError("unsupported duration_unit")
    return float(record["duration_value"]) * (60 if unit == "minutes" else 1)
