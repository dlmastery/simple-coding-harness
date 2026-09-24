from engine import build as build_pipeline

FAMILY = 'linear'
TRANSFORM = 'quadratic'
STRENGTH = 0.45000000000000007
STAGE = 6

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
