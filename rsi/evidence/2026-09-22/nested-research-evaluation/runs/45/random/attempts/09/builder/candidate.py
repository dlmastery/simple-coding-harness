from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'base:neighbors-25', 2.3580154, seed)
