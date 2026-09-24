from engine import build as build_pipeline

FAMILY = 'boost'
TRANSFORM = 'quadratic'
STRENGTH = 4.5
STAGE = 5

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
