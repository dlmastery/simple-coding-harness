"""The budget: n fits, then it refuses. No tool has another way to fit.

An off switch that is an object, not a sentence in a README: the 25th
`fit_recipe` gets an `Error:` result, and `used` is the count every claim
quotes. FREEZE is the moment the budget is spent: `score_test` opens then and
`write_card` closes then.
"""


class BudgetExhausted(RuntimeError):
    pass


class Budget:
    def __init__(self, n):
        self.n = n
        self.used = 0

    @property
    def left(self):
        return self.n - self.used

    @property
    def frozen(self):
        """FREEZE: every fit is spent. The test split may be scored once, the memory may not change."""
        return self.used >= self.n

    def spend(self):
        """Count one fit before it happens. An error still counts: a wasted fit is a fit."""
        if self.frozen:
            raise BudgetExhausted(f"budget of {self.n} fits used; fit {self.used + 1} refused")
        self.used += 1
        return self.used
