def prepare(record):
    result = {k: v for k, v in record.items() if k != "details"}
    unit = result.get("duration_unit")
    if unit in ("seconds", "minutes"):
        result["duration_seconds"] = float(result.pop("duration_value")) * (60 if unit == "minutes" else 1)
        result.pop("duration_unit")
    return result
