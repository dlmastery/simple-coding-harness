"""The locked test: the test split is scored once, through this object, after
FREEZE, and a second call raises. It is the anti-peek gate: a search loop that
could score the test split twice could tune on it.
"""


class TestLocked(RuntimeError):
    pass


class LockedTest:
    def __init__(self, score, budget):
        self._score = score     # score(recipe) -> the test score; the gate is its only holder
        self._budget = budget   # FREEZE is the budget being spent; the gate asks it
        self.result = None

    def score_once(self, recipe):
        if not self._budget.frozen:
            raise TestLocked(f"the test split is locked until FREEZE: {self._budget.left} fits remain")
        if self.result is not None:
            raise TestLocked("the test split was scored once already; there is no second look")
        self.result = {"recipe": recipe, "test_score": self._score(recipe)}
        return self.result["test_score"]
