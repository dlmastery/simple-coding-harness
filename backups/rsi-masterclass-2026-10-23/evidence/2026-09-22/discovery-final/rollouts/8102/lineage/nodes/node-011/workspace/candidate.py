from engine import build as build_pipeline

FAMILY = 'extra'
TRANSFORM = 'pairwise'
STRENGTH = 3.0
STAGE = 2

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
