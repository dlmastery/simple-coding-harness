# 10.14 · Simulate Self-HPO Alternation

**Purpose:** See harness-policy optimization.

## Simplified Simulation

```python
class SelfHPO:
    def h_step(self, policy):
        # Policy analyzes failures, proposes harness
        pass
    
    def p_step(self, policy, harness):
        # Update policy under selected harness
        pass
```

## Your Task

Implement alternating H-step and P-step on a toy task.

## Next

[Group 05 · Environments & Metrics](../05_environments_metrics/README.md)
