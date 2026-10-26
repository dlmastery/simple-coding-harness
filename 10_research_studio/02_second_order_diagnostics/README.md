# Second-Order RSI: Diagnostic Inquiry

**Group 02 · October 2026 Paper: arXiv:2610.05701**  
**Your place:** Why do failures occur before patching? 3 labs; 1.5–2.5 hours.

## Purpose

The SO-RSI paper introduces second-order diagnostic inquiry—investigating WHY failures occur before committing to structural interventions. This group explores anomaly detection and diagnostic probes.

## Labs

| Lab | Focus | Why it matters |
|------|-------|----------------|
| [10.06 · Run the SO-RSI demo](step_01_run_demo/README.md) | Execute the laptop demo | See anomaly detection in action |
| [10.07 · Analyze diagnostic probes](step_02_analyze_probes/README.md) | Understand three anomaly types | Learn when each probe triggers |
| [10.08 · Apply to debugging task](step_03_apply/README.md) | Use diagnostics on your own task | Test practical utility |

## Starting Evidence

You have:
- Full laptop demo: `../../12_october_2026_papers/02_second_order_rsi/demo.py`
- Paper summary in `../../12_october_2026_papers/PAPER_SUMMARIES.md`
- Demo guide in `../../12_october_2026_papers/LAPTOP_DEMOS.md`

## What You Will Learn

By the end of this group, you should be able to:
- Detect structural anomalies in execution traces
- Run diagnostic probes for recurrence, opposing edits, and mismatch
- Explain why second-order inquiry improves over first-order patching
- Apply SO-RSI principles to debugging workflows

## Key Mechanism

**Three structural anomalies:**
1. **Recurrence**: Same fix attempted repeatedly without success
2. **Opposing edits**: System oscillates between conflicting solutions
3. **Expectation mismatch**: Outcome violates expected behavior

**Diagnostic probes:**
- Recurrence → Investigate underlying constraint/assumption
- Opposing → Identify conflicting constraints
- Mismatch → Update environment/task assumptions

**Inquiry memory:**
- Accumulate causal evidence across RSI rounds
- Guide systematic workflow edits instead of symptom patches

## Next

Start with [10.06 · Run the SO-RSI demo](step_01_run_demo/README.md).
