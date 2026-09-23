from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:extra-leaf5', 0.18259058, seed)
