"""Performance-cost trade-offs over an archive of harnesses (the HarnessPro idea).

Instead of one winner, keep the Pareto front of (score up, cost down) and pick
three operating points with a normalized weighted squared distance to the
ideal corner:

    lite    weights cost most
    medium  balances both
    heavy   weights score most
"""

PROFILES = {"lite": 0.1, "medium": 0.5, "heavy": 0.9}  # weight on score; the rest is on cost


def front(points):
    """points: [(id, score, cost)]. Keep those no other point beats on both axes."""
    keep = []
    for i, s, c in points:
        dominated = any((s2 >= s and c2 <= c) and (s2 > s or c2 < c) for _, s2, c2 in points)
        if not dominated:
            keep.append((i, s, c))
    return sorted(keep, key=lambda p: p[2])


def pick(points, w_score):
    """Closest point to (best score, lowest cost) after scaling both axes to [0, 1]."""
    s_lo, s_hi = min(p[1] for p in points), max(p[1] for p in points)
    c_lo, c_hi = min(p[2] for p in points), max(p[2] for p in points)

    def dist(p):
        ds = (s_hi - p[1]) / ((s_hi - s_lo) or 1)
        dc = (p[2] - c_lo) / ((c_hi - c_lo) or 1)
        return w_score * ds ** 2 + (1 - w_score) * dc ** 2

    return min(points, key=dist)


def profiles(points):
    f = front(points)
    return {name: pick(f, w) for name, w in PROFILES.items()}
