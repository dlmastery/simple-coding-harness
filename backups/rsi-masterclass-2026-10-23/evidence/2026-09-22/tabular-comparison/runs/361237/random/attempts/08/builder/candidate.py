from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:svr-tight', 0.21993384, seed)
