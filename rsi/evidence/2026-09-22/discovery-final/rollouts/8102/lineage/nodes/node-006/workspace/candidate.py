from engine import build as build_pipeline

FAMILY = 'extra'
TRANSFORM = 'raw'
STRENGTH = 1.0
STAGE = 0

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)
