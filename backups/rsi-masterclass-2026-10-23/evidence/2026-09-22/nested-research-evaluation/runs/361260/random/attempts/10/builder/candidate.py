from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:absolute-forest', 0.14741528, seed)
