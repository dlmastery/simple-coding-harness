"""Ablation: fixed broad allocation with the development-learned stop rule.

Written before evaluation. Shares the evolved policy's 0.20 threshold.
"""


def choose(view):
    if view.best_loss is not None and view.best_loss <= .20:
        return None
    roots = [item.node for item in view.observations if item.parent == "root"]
    if len(roots) < 3:
        return "root"
    lookup = {item.node: item for item in view.observations}

    def depth(node):
        count = 0
        while node != "root":
            count += 1
            node = lookup[node].parent
        return count

    leaves = [node for node in view.eligible if node != "root"]
    return min(leaves, key=lambda node: (depth(node), node))
