"""A complete twelve-fit researcher; execution and checks are supplied by the host."""
import random

MODE = "parent"
FIRST_FACTOR = 0.5
BREADTH = 0
RANKING = {"classification": [], "regression": []}
PREFIX = {
    "classification": ["base:linear", "base:extra-trees", "base:rbf-1", "base:hist-boost",
                       "base:random-forest", "base:rbf-10", "base:neighbors-5", "base:neighbors-25"],
    "regression": ["one:median-reference", "base:linear", "base:random-forest", "base:rbf-1",
                   "base:extra-trees", "base:hist-boost", "base:rbf-10", "base:neighbors-5"],
}
EXTRA = {
    "classification": ["one:rbf-unscaled", "one:rbf-wide", "one:extra-leaf2", "one:boost-regularized",
                       "two:unscaled-c1", "two:unscaled-c100", "two:forest-all-features", "two:native-category-boost"],
    "regression": ["one:median-reference", "one:absolute-boost", "one:absolute-forest", "one:svr-tight",
                   "two:log-boost", "two:log-svr", "two:extra-leaf5", "two:quadratic-splines"],
}
FIXED_TAIL = {
    "classification": ["one:rbf-wide", "one:boost-regularized", "two:unscaled-c100", "two:native-category-boost"],
    "regression": ["one:absolute-boost", "two:quadratic-splines", "two:extra-leaf5", "one:svr-tight"],
}


def pool(kind, nonnegative):
    base = ["base:" + name for name in ("linear", "extra-trees", "hist-boost", "random-forest", "rbf-1", "rbf-10", "neighbors-5", "neighbors-25")]
    return [name for name in base + EXTRA[kind] if nonnegative or name not in {"two:log-boost", "two:log-svr"}]


def family(template):
    if any(key in template for key in ("rbf", "svr", "unscaled")):
        return "kernel"
    if "forest" in template or "extra" in template:
        return "forest"
    if "boost" in template:
        return "boost"
    if "neighbor" in template:
        return "neighbors"
    return "linear" if "median" not in template else "reference"


def winner(history):
    valid = [row for row in history if row["status"] == "success"]
    if not valid:
        raise ValueError("No valid model; preserve the failed researcher")
    return min(valid, key=lambda row: (row["selection_loss"], row["step"]))


def plan(template, factor=1., parent_step=0, reason="broad conventional probe"):
    return dict(template=template, factor=round(min(20., max(.05, factor)), 8), parent_step=parent_step, reason=reason)


# BEGIN REWRITABLE PROPOSER
def adaptive(history, kind, serial, nonnegative, unavailable):
    valid = [row for row in history if row["status"] == "success" and "median" not in row["template"]]
    if not valid:
        raise ValueError("No successful tunable model")
    parent = min(valid, key=lambda row: (row["selection_loss"], row["step"]))
    factors = (FIRST_FACTOR, .5, 2., .25, 4., .75, 1.5, .125, 8.)
    factor = parent["factor"] * factors[(serial-9) % len(factors)]
    return plan(parent["template"], factor, parent["step"], "refine current best checked model")
# END REWRITABLE PROPOSER


def research(task, kind, nonnegative, execute, record_rejection):
    """Own the search loop, feedback-dependent proposals and model retention."""
    history = []
    unavailable = set()
    rng = random.Random(9173 + int(task))
    for serial in range(1, 129):
        if len(history) == 12:
            return history, winner(history)
        if len(history) < 8:
            candidate = plan(PREFIX[kind][len(history)])
        elif MODE == "fixed":
            candidate = plan(FIXED_TAIL[kind][len(history)-8], reason="fixed expanded portfolio")
        elif MODE == "random":
            choices = [name for name in pool(kind, nonnegative) if "median" not in name]
            candidate = plan(rng.choice(choices), 10**rng.uniform(-1, 1), reason="seeded full-space random search")
        else:
            candidate = adaptive(history, kind, serial, nonnegative, unavailable)
        result = execute(candidate, serial, len(history)+1)
        if result["status"] == "duplicate-constructor":
            record_rejection(candidate, serial, result)
            if candidate["factor"] == 1:
                unavailable.add(candidate["template"])
            # Fixed probes must be distinct; do not silently substitute another model.
            if len(history) < 8 or MODE == "fixed":
                raise ValueError("Fixed constructor collision; preserve and inspect")
        else:
            history.append(result)
    if len(history) == 12:
        return history, winner(history)
    raise ValueError("128 proposals exhausted before twelve attempts")
