from engine import build as build_pipeline

FAMILY = 'boost'
TRANSFORM = 'quadratic'
STRENGTH = 20.25
STAGE = 8

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
