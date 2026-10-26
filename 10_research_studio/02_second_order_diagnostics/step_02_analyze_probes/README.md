# 10.07 · Analyze Diagnostic Probes

**Purpose:** Understand the three anomaly types and their probes.

## Three Anomaly Types

### 1. Recurrence

**Detection:** Same fix attempted repeatedly with failure

**Example:**
```
Attempt 1: Add parameter X → failure
Attempt 2: Add parameter X → failure
Attempt 3: Add parameter X → failure
```

**Diagnostic probe:** Investigate underlying constraint or assumption

**Root cause questions:**
- Is parameter X actually needed?
- Is the parameter name correct?
- Is there a type mismatch?
- Is there a dependency missing?

### 2. Opposing Edits

**Detection:** System oscillates between conflicting solutions

**Example:**
```
Attempt 1: Increase learning rate → failure
Attempt 2: Decrease learning rate → failure
Attempt 3: Increase learning rate → failure
```

**Diagnostic probe:** Identify conflicting constraints

**Root cause questions:**
- Are there contradictory requirements?
- Is the objective function ill-specified?
- Are there hidden constraints?
- Is the search space mis-specified?

### 3. Expectation Mismatch

**Detection:** Outcome violates expected behavior

**Example:**
```
Attempt: Add regularization
Expected: Reduces overfitting
Actual: Training error increases
```

**Diagnostic probe:** Update environment/task assumptions

**Root cause questions:**
- Is the model of the environment wrong?
- Are task dynamics misunderstood?
- Is the metric misaligned with objectives?
- Are there external factors unaccounted for?

## Your Task

1. Run the demo and count how many times each anomaly type triggers
2. For each anomaly, write down the diagnostic recommendation
3. Explain why that recommendation addresses the root cause

## Expected Output

A table showing:
| Anomaly type | Count in demo | Typical recommendation | Why it helps |

## Quiz

**Q1:** Can multiple anomalies trigger simultaneously?

**A1:** Yes. A single execution trace could show recurrence (same fix repeated), opposing (undoing previous change), and mismatch (unexpected outcome) all at once. The system should trigger all relevant probes.

**Q2:** What happens if a diagnostic probe finds no clear root cause?

**A1:** The inquiry memory records the inconclusive result. Future traces with similar patterns can build evidence. If enough inconclusive probes accumulate, the system may need to revise its diagnostic assumptions or try broader exploration.

## Next Step

[10.08 · Apply to debugging task](../step_03_apply/README.md)
