def prepare(record):
    result = dict(record)
    if len(result.get("details", "")) > 40:
        result = {k: v for k, v in result.items() if k not in ("details", "candidate")}
    return result
