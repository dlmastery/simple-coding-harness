from engine import build as build_pipeline

FAMILY = 'linear'
TRANSFORM = 'quadratic'
STRENGTH = 0.1
STAGE = 3

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
