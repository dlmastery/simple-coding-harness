from engine import build as build_pipeline

FAMILY = 'boost'
TRANSFORM = 'quadratic'
STRENGTH = 13.5
STAGE = 6

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
