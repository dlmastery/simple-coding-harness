from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:extra-leaf2', 0.49542675, seed)
