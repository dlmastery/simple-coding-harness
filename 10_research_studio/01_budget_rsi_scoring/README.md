# Budget RSI: Scoring Code Edits Before Running

**Group 01 · October 2026 Paper: arXiv:2610.29121**  
**Your place:** Can we score code edits before full evaluation? 3 labs; 1.5–2.5 hours.

## Purpose

The Budget RSI paper introduces a linear readout scorer that predicts held-out performance from a steering split, avoiding expensive full evaluation of every candidate. This group explores that mechanism.

## Labs

| Lab | Focus | Why it matters |
|------|-------|----------------|
| [10.03 · Run the Budget RSI demo](step_01_run_demo/README.md) | Execute the laptop demo | See the mechanism in action |
| [10.04 · Analyze the scoring mechanism](step_02_analyze_mechanism/README.md) | Understand linear readout | Learn how features drive predictions |
| [10.05 · Extend to your own edits](step_03_extend/README.md) | Apply to a new task | Test transferability |

## Starting Evidence

You have:
- Full laptop demo: `../../12_october_2026_papers/01_budget_rsi/demo.py`
- Paper summary in `../../12_october_2026_papers/PAPER_SUMMARIES.md`
- Demo guide in `../../12_october_2026_papers/LAPTOP_DEMOS.md`

## What You Will Learn

By the end of this group, you should be able to:
- Run the Budget RSI scorer on synthetic edits
- Explain how steering splits enable pre-evaluation
- Identify which diff features matter most
- Adapt the scorer to a new code editing task

## Key Mechanism

**Linear readout scoring:**
1. Reserve a steering split (e.g., 48/164 test instances)
2. Extract 8 diff features from proposed edit
3. Train linear model: score = w^T × [parent_rate, diff_features]
4. Score new edits before full evaluation
5. Select best-scored edit to expand

**Cost savings:**
- Full evaluation: 128 edits × 100 instances = 12,800 evaluations
- Budget RSI: 96 training × 16 + 32 scoring × 0 = 1,536 evaluations
- ~88% reduction in compute

## Next

Start with [10.03 · Run the Budget RSI demo](step_01_run_demo/README.md).
