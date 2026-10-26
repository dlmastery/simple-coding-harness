# 10.02 · Audit an October 2026 Paper

**Purpose:** Check what the paper actually measured.

## What This Lab Teaches

Auditing a paper means answering:
- What objects changed? (Task model, research skill, improver, evaluator)
- What feedback connected them? (Scores, traces, human input)
- What evaluation protocol was used? (Partitions, metrics, checkpoints)
- What costs were incurred? (Compute, time, inference)
- What assumptions remain untested? (Generalization, robustness, scale)

## Audit Template

For any October 2026 paper, complete this table:

| Aspect | Paper's Setup | Laptop Adaptation | What's Preserved |
|--------|--------------|------------------|------------------|
| Changed object | | | |
| Feedback type | | | |
| Evaluation protocol | | | |
| Compute budget | | | |
| Untested assumptions | | | |

## Example: SO-RSI Paper

| Aspect | Paper's Setup | Laptop Adaptation | What's Preserved |
|--------|--------------|------------------|------------------|
| Changed object | Workflow edits (second-order) | Synthetic trace modifications | Diagnostic inquiry concept |
| Feedback type | Execution traces from Lean 4/Verus | Synthetic execution traces | Anomaly detection logic |
| Evaluation protocol | 24-hour search, held-out proofs | 20-iteration simulation | Comparative improvement |
| Compute budget | 24 hours per comparison | < 2 minutes | Mechanism demonstration |
| Untested assumptions | Generalizes to other formal systems | Only synthetic traces | Second-order principle |

## Your Task

1. Choose one October 2026 paper (from the 9 in summaries)
2. Read its full summary in `../../12_october_2026_papers/PAPER_SUMMARIES.md`
3. Complete the audit template for that paper
4. Identify one assumption the paper makes but doesn't test

## Expected Output

A document `paper_audit_[paper_name].md` with:
- Completed audit template
- List of untested assumptions
- Laptop adaptation constraints
- What would be needed to test the assumptions

## Quiz

**Q1:** Why is it important to identify untested assumptions before implementing?

**A1:** Because implementation effort should focus on testing the most uncertain aspects. If an assumption is foundational but untested, the implementation should include checks or ablations to validate it.

**Q2:** Can a laptop adaptation ever prove a paper's headline claim?

**A2:** No. A laptop adaptation demonstrates the mechanism but cannot prove the headline result because it uses different scale, data, and evaluation conditions. It can show the mechanism is sound, but not that it achieves the paper's reported performance.

## Next Step

[Group 01 · Budget RSI: Scoring Before Running](../01_budget_rsi_scoring/README.md)
