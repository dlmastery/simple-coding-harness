"""Fixed broad-exploration control. No learning between rollouts."""


def choose(view):
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
