# 10.01 · Distinguish Claim from Evidence

**Purpose:** A headline score does not prove the mechanism.

## What This Lab Teaches

Reading an October 2026 RSI paper requires separating:
- **What the paper claims** (headlines, abstract conclusions)
- **What the paper measured** (actual experiments, reported results)
- **What remains untested** (suggestions, future work, implications)

## Example: Budget RSI Paper

**Headline claim:** "Scoring code edits before they run achieves 87.0% on HumanEval+"

**What was actually measured:**
- GPT-4o as the base model
- 96 training edits (16-instance fit split)
- Steering split of 48/164 HumanEval+ instances
- Linear readout scoring on 8 diff features
- One specific selection strategy (Huxley–Gödel Machine)

**What remains untested:**
- Other base models (Claude, Llama, etc.)
- Other selection strategies
- Real-world code editing tasks beyond HumanEval+
- Longer search horizons or different budgets
- Transfer to other benchmarks (Polyglot, etc.)

**Laptop adaptation preserves:**
- The linear readout mechanism
- Steering split concept
- Selection strategy logic

**Laptop adaptation does NOT preserve:**
- GPT-4o's actual performance
- HumanEval+ difficulty
- Real diff feature complexity

## Your Task

1. Read the Budget RSI paper summary in `../../12_october_2026_papers/PAPER_SUMMARIES.md`
2. Identify three claims the paper makes
3. For each claim, state:
   - What experiment supports it
   - What conditions limit it
   - What the laptop demo preserves vs. changes

## Expected Output

A short document `claim_evidence_analysis.md` with:
- Three paper claims
- Supporting evidence for each
- Limitations of each claim
- Laptop adaptation mapping

## Quiz

**Q1:** Can the Budget RSI paper claim that linear readout scoring works for all code editing tasks?

**A1:** No. The paper only tested on HumanEval+ and Polyglot with GPT-4o. Different tasks, models, or benchmarks may behave differently.

**Q2:** Why does the laptop demo use synthetic edits instead of real code diffs?

**A2:** To demonstrate the mechanism without requiring access to GPT-4o, full HumanEval+ dataset, or complex diff parsing. The demo preserves the concept while making it laptop-executable.

## Next Step

[10.02 · Audit an October 2026 paper](../step_02_audit_paper/README.md)
