# The research behind each lab

[Course](README.md)

State of the art as of **23 October 2026**. Each entry gives what the paper
changes, what evidence it uses, and the lab that rebuilds its mechanism at
laptop scale. Numbers are the papers' own reported results, not ours. Our
labs reproduce a mechanism, never a headline.

## The frame: what is being improved?

Every system below keeps the model's weights fixed (except where noted) and
changes the **harness**: the prompts, skills, memory, tools, control loop and
selection rules around the model. The recursive question is whether the
procedure that *changes the harness* can itself be improved, and whether the
improved procedure then governs later improvement.

| Object that changes | Example | Lab |
|---|---|---|
| A model's output (one submission) | the agent's training script | 01 |
| The harness (prompts, skills, config) | Meta-Harness, RRSI, HarnessPro | 03–06 |
| The harness, online, per task, with a library that learns how to edit | Harness² | 07 |
| The improver that edits harnesses | AIDE², Gödel-machine family | 08 |
| Harness and weights together | Self-HPO, MASS, SafeEvolve | 08 (discussion) |

## Foundations the labs assume

- **MLE-bench** (Chan et al., OpenAI, arXiv [2410.07095](https://arxiv.org/abs/2410.07095)). 75 Kaggle competitions with official graders and human leaderboards; the 22-competition *Lite* split is the standard low-complexity subset. **Our benchmark**: seven CPU-friendly Lite competitions, graded by MLE-bench itself.
- **AIDE** (Jiang et al., arXiv [2502.13138](https://arxiv.org/abs/2502.13138)). ML engineering as tree search over code: draft, debug, improve. **Our agent** is a small AIDE-style loop whose every prompt and setting lives in an editable harness file.
- **Darwin Gödel Machine** (Zhang et al., arXiv [2505.22954](https://arxiv.org/abs/2505.22954)). A coding agent edits its own code and keeps an open-ended archive of variants, validated empirically instead of proved. Lab 08 uses its archive idea.

## Lab 03–04: search over harness code with full history

**Meta-Harness** (Lee, Nair, Zhang, Lee, Khattab, Finn, arXiv [2603.28052](https://arxiv.org/abs/2603.28052), March 2026). An agentic proposer searches over harness code. It reads the source, scores and **raw execution traces of every earlier candidate through a filesystem**, instead of a compressed summary. Reports +7.7 points on online text classification with 4× fewer context tokens, and +4.7 points on 200 IMO-level problems across five held-out models. It is the baseline almost every later paper compares against.
→ Lab 03 builds the loop and archive; lab 04 compares a proposer that sees only scores against one that reads raw traces.

## Lab 05: why naive harness evolution overfits, and how to regularize it

**RRSI: Regularized Recursive Self-Improvement of Agent Harnesses** (Xia, …, Pfister, Lee, Google, arXiv [2609.24972](https://arxiv.org/abs/2609.24972), v3 4 Oct 2026). Reusing one finite evolve set adaptively lets evolution promote noise, benchmark-specific fitting and accumulated complexity. RRSI keeps the edit space open but regularizes both sides:
- *proposal*: an edit budget that shrinks on a cosine schedule, `b_t = ⌈b_min + (b_max − b_min)·½(1 + cos(πt/T))⌉`, so late edits are small and attributable; a **critic** that rejects diffs encoding task names, entities, task-specific values or inert machinery *before* they are evaluated; a **pruner** that deletes components with no positive measured gain over a recent window (an L1/Lasso analogy);
- *selection*: a noise-adjusted floor `S(H′) ≥ S* − δ` and a cost rule for gains above noise, `ΔC ≤ β₀ + β₁ΔS`.

On Harvey LAB, Meta-Harness reaches the highest evolve score (93.0) but RRSI has the best out-of-distribution average (43.6 vs 40.6) with about 30% fewer policy tokens. Two baselines (AHE, TTHE) end *below the unchanged harness* out of distribution despite evolve-set gains.
→ Lab 05 turns on each regularizer in turn and measures evolve versus held-out versus OOD.

**Bad Genius / CHASE** (Zhu et al., arXiv [2609.18366](https://arxiv.org/abs/2609.18366), Sept 2026). Holding out *tasks* does not hold out the *benchmark protocol*. A Challenger searches for semantics-preserving protocol transformations that destroy a harness's gain; surviving counterfactuals are archived and constrain later search.
→ Lab 05 uses MLE-bench's own obfuscated descriptions (same task, no competition name) as a counterfactual: a harness that wins by recognizing Kaggle competitions loses its gain there.

**HackProbe** (Yang et al., arXiv [2609.04665](https://arxiv.org/abs/2609.04665), Sept 2026). A black-box monitor for self-evolving loops: a secret fixed-distribution comparison core plus a rotating fresh layer, with tests for level gap, divergence, stagnation and confidently-wrong rate. Reported AUROC 0.763 versus 0.663 for the strongest baseline.
→ Lab 05's held-out split plays the secret core: the proposer never sees it, and we watch the gap.

**Auditing Harness Tampering** (arXiv [2609.00069](https://arxiv.org/abs/2609.00069), Sept 2026). Self-modifications can produce illusory gains or break integrity constraints (authorization, provenance, completeness); tampering appears in real runs and often persists in the best agent's lineage.
→ Lab 09 audits the lineage of every accepted harness.

## Lab 06: one harness is not enough

**HarnessPro** (Pan, …, Tang, arXiv [2610.26770](https://arxiv.org/abs/2610.26770), 19 Oct 2026). Label-free recursive harness improvement that optimizes performance *and* execution cost. Specialized agents diagnose trajectories, plan with different performance–cost priorities, and implement candidates scored by LLM-generated tests. It returns three harnesses (**lite, medium, heavy**) chosen by normalized weighted squared distance. Heavy mode: +2.0 pass-rate points and −26.1% cost per task versus the RHO baseline (GPT-5.5 with Codex) on Terminal-Bench 2, SWE-Bench Pro and ProgramBench.
→ Lab 06 builds the Pareto front of the archive and picks lite, medium and heavy.

**MaD-RSI: Model-as-Data** (Cui et al., arXiv [2610.28201](https://arxiv.org/abs/2610.28201), 20 Oct 2026). RSI ties a harness to the one model it was tuned with. MaD-RSI optimizes one shared harness on the failure trajectories of several heterogeneous models, using model differences as training evidence instead of a post-hoc check.
→ Lab 06 tests whether the evolved harness transfers from `gpt-5.4-nano` to a different frozen model.

**Mixture of Self-Improving Branches** (Dong et al., arXiv [2609.37834](https://arxiv.org/abs/2609.37834), Sept 2026). Splits harness search into branches with their own development subsets and proposal policies, plus a router that picks a branch head per input. Reported relative gains over Meta-Harness: 11.6% on Terminal-Bench 2.0, 3.8% on SWE-bench Lite.
→ Lab 06 extension exercise.

## Lab 07: the open world, with no verifier

**Harness²: Recursive Agent Harnessing for an Open World** (Xu, Lee, Pfister, et al., Google, arXiv [2610.14224](https://arxiv.org/abs/2610.14224), 9 Oct 2026; code github.com/google-research/harness2). Tasks arrive one at a time with no ground-truth verifier. A **contrastive improvement step** runs the current harness once as a reference, proposes an *invariant* candidate (planning, tool use, context) and a *domain* candidate, probes both on the same task, and a composer merges what the *behavioral contrast* supports. After each task, lessons supported by contrast go into an **improvement library** (an executable harness plus `EXPERIENCE.md`), which shapes how later harnesses are edited. That second loop is the recursion. Parallel recursion with budget k widens one step. One step improves GLM-5 on WorkBuddy-Bench from 64.2 to 75.7; ablating the library costs 3.1 points. The paper is explicit that contrasts guide edits but do not verify correctness.
→ Lab 07 rebuilds the contrastive step and the library on a stream of competitions where the agent never sees a grade.

## Lab 08: improving the improver

**AIDE²: Recursive self-improvement of AI research agents** (Srikanth, Zhao, Xu, Wu, Jiang, Weco, arXiv [2609.26457](https://arxiv.org/abs/2609.26457), Sept 2026). The research agent optimizes its own code, so each accepted rewrite becomes the agent that makes the next edit. An autonomous 8-day run found seven successive improvements (a new search policy, context-compression memory); gains transferred to four held-out benchmarks. The rate of reward hacking on a held-out family *fell* from 55% to 32% without being optimized.

**Recursive Self-Improvement on a Budget** (Darzi et al., arXiv [2610.29121](https://arxiv.org/abs/2610.29121), 21 Oct 2026). Scores proposed scaffold edits *before* running them with a frozen linear readout over the parent's solve rate and diff features, inside Huxley-Gödel-Machine-style selection (Thompson sampling over evaluated nodes).

**Self-HPO: harness–policy co-evolution** (Wei, …, Gao, arXiv [2610.22791](https://arxiv.org/abs/2610.22791), 16 Oct 2026). Alternates an H-step (the policy proposes harnesses from its own failures) with a P-step (RL on the policy under the chosen harness); hard tasks found in training seed the next harness search. Qwen3.5-35B-A3B: 57.8% → 64.8% average resolve rate, and the joint gain exceeds the sum of the separate gains. **MASS** (Lee et al., arXiv [2610.12176](https://arxiv.org/abs/2610.12176), 8 Oct 2026) alternates multi-agent workflow evolution with fine-tuning on self-generated trajectories for non-verifiable tasks.
→ Lab 08 makes the improver's own protocol an editable file, revises it from the improver's run log, and tests whether the revised improver produces better harnesses on competitions neither improver saw. Weight updates are out of scope on a laptop; the lab explains exactly what they would add.

## Further reading

- **ScholarEvolve: Learning from Research** (arXiv [2609.40169](https://arxiv.org/abs/2609.40169)): retrieve published techniques to guide harness modules, instead of reacting only to failures.
- **Evo-Bench** (arXiv [2608.09096](https://arxiv.org/abs/2608.09096)): strict sandbox separation; the evolver may read validation artifacts but write only its own harness. Our `edits.py` follows this rule.
- **Recursive Harness Self-Improvement for Reasoning Data Synthesis** (arXiv [2610.03548](https://arxiv.org/abs/2610.03548)), **SciΠvot** (arXiv [2610.21082](https://arxiv.org/abs/2610.21082)), and the curated list [Awesome-Harness-Self-Improvement](https://github.com/leezythu/Awesome-Harness-Self-Improvement).
