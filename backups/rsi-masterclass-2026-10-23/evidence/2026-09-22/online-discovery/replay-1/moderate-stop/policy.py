"""Agent-proposed revision 6: tighten the quality threshold slightly.

Developed from generation-0 trees only. No task identifier or hidden score.
"""


def choose(view):
    if view.best_loss is not None and view.best_loss <= .18:
        return None
    roots = [item.node for item in view.observations if item.parent == "root"]
    if not roots:
        return "root"
    lookup = {item.node: item for item in view.observations}

    def ancestry(node):
        depth = 0
        while lookup[node].parent != "root":
            depth += 1
            node = lookup[node].parent
        return node, depth + 1

    leaves = [item for item in view.observations if item.node in view.eligible]
    first = next(item for item in leaves if ancestry(item.node)[0] == roots[0])
    if ancestry(first.node)[1] < 4:
        return first.node
    if len(roots) < 3:
        return "root"
    available = [item for item in leaves if ancestry(item.node)[1] < 4]
    if not available:
        return None
    return min(available, key=lambda item: float("inf") if item.loss is None else item.loss).node
