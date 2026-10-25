def prepare(record):
    return {k: v for k, v in record.items() if k != "details"}
