def prepare(record):
    result = dict(record)
    if len(result.get("details", "")) > 40:
        result.pop("details", None)
    return result
