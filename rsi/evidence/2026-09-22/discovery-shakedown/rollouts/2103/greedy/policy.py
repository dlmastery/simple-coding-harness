"""Fixed diverse-draft, best-observed-leaf control."""


def choose(view):
    if sum(item.parent == "root" for item in view.observations) < 3:
        return "root"
    valid = [item for item in view.observations if item.node in view.eligible and item.loss is not None]
    return min(valid, key=lambda item: item.loss).node if valid else "root"
