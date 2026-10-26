# October 2026 RSI Paper Summaries

Complete analysis of 9 October 2026 RSI papers with mechanisms, benchmarks, and laptop adaptation notes.

---

## 1. Recursive Self-Improvement on a Budget: Scoring Code Edits Before They Run

**arXiv**: 2610.29121 (October 21, 2026)  
**Authors**: Erfan Darzi (Harvard/MIT), Sree Bhargavi Balija (UCSD), Sheng He (Harvard)

### Core Idea
A coding agent must choose which proposed edit to expand before evaluation. This paper introduces a **linear readout scorer** that predicts held-out performance from a steering split, avoiding expensive full evaluation of every candidate.

### Key Mechanism
1. **Steering split**: Reserve a subset of test instances (e.g., 48/164 for HumanEval+)
2. **Edit features**: 8 coordinates from the proposed diff (additions, deletions, file changes, etc.)
3. **Linear readout**: Score = w^T × [parent_solve_rate, diff_features]
4. **Huxley–Gödel Machine selection**: Thompson sampling on steering counts of evaluated nodes
5. **Budget constraint**: Each run fits one linear readout from 96 labeled edits (16-instance fit split)

### Results
- **HumanEval+**: GPT-4o reaches 87.0% held-out (vs 84.2% parent-rate ablation)
- **Polyglot**: Similar gains on multi-language benchmarks
- **Cost reduction**: Scores 100+ edits in seconds vs hours of full evaluation

### Laptop Adaptation
✅ **Fully laptop-executable**
- Use small subset of HumanEval+ (e.g., 20 problems)
- Simplified diff features (lines added/deleted, files changed)
- Pure NumPy linear regression (no GPU)
- Runtime: < 5 minutes for 100 edits

### Demo Location
`01_budget_rsi/demo.py` - Complete implementation with synthetic code edits

---

## 2. Second-Order Problem Solving for Recursive Self-Improvement (SO-RSI)

**arXiv**: 2610.05701 (October 7, 2026)  
**Authors**: Yuxuan Jiang (UMBC), Aditya Vempaty, Ashish Jagmohan (Emergence AI)

### Core Idea
Standard RSI is a **first-order optimizer**: it patches surface parameters in response to failure symptoms, leading to trial-and-error thrashing. SO-RSI elevates this to **second-order diagnostic inquiry**—investigating WHY failures occur before committing to structural interventions.

### Key Mechanism
1. **Structural anomaly detection**: Monitor traces for:
   - **Recurrence**: Same fix attempted repeatedly
   - **Opposing edits**: Undoing previous changes
   - **Expectation mismatch**: Outcome violates predictions
2. **Diagnostic probes**: Lightweight tests to investigate root causes
3. **Inquiry memory**: Persistent causal evidence across RSI rounds
4. **Systematic edits**: Address mechanisms, not symptoms

### Results
- **Lean 4 proof generation**: +21.8% held-out pass rate over Naive RSI
- **Verus code verification**: +25.8% held-out pass rate
- **Behavioral analysis**: Reduced thrashing, fewer oscillations

### Laptop Adaptation
✅ **Fully laptop-executable**
- Use synthetic execution traces (code attempts, failures, fixes)
- Simple anomaly detection (pattern matching on trace history)
- Diagnostic probes as string/AST analysis
- Runtime: < 2 minutes for 50 traces

### Demo Location
`02_second_order_rsi/demo.py` - Anomaly detector with diagnostic probes

---

## 3. AReaL-RSI: Adaptive Scaling and Coordination of Recursive Self-Improvement

**arXiv**: 2610.18083 (October 15, 2026)  
**Authors**: Wenhao Zhou et al. (Ant Group, Zhejiang University, HKUST)

### Core Idea
Scaling RSI requires organizing a **persistent research team of agents** without updating backbone LLM weights. The framework coordinates leader agents, researcher roles, and conditional memory sharing.

### Key Mechanism
1. **Leader agent**: Selects task-appropriate research orientations
2. **Conditional memory sharing**: Distinguishes unresolved problems from supported findings
3. **Evidence-based review**: After each campaign, revises orientation, knowledge, and skills
4. **Specialized roles**: Different agents for exploration, verification, integration

### Results
- **Terminal Bench**: +2.2 percentage points per backbone
- **KernelBench**: +32.2–36.8% mean speedup
- **Scaling efficiency**: Experience sharing beats independent exploration by 1.9–27.5%

### Laptop Adaptation
⚠️ **Partial (mechanism analysis only)**
- Implement simple leader-follower coordination (3 agents)
- Use toy tasks (e.g., numerical optimization)
- Conditional memory as shared dictionary with flags
- Runtime: ~10 minutes for 5 campaigns

### Demo Location
`03_areal_rsi/mechanism_demo.py` - Simplified multi-agent coordination

---

## 4. RSIFlow: Adaptive Self-Improvement Workflows with an Evolving Meta-Agent

**arXiv**: 2610.21791 (October 17, 2026)  
**Authors**: Huan Zhang et al. (Beihang University, Tsinghua, BAAI)

### Core Idea
Adapting self-improvement workflows to evolving performance bottlenecks while improving workflow orchestration through execution feedback. Integrates adaptive workflow orchestration with meta-agent capability evolution.

### Key Mechanism
1. **Evolving meta-agent**: Coordinates workflow orchestration
2. **Adaptive bottleneck targeting**: Identify and focus on current limitations
3. **Workflow orchestration**: Dynamic routing of improvement actions
4. **Execution feedback loop**: Workflow learns from its own performance

### Laptop Adaptation
⚠️ **Partial (workflow simulation only)**
- Simulate workflow as graph of improvement steps
- Meta-agent as rule-based orchestrator
- Bottleneck detection via performance profiling
- Runtime: ~5 minutes for 20 workflow cycles

### Demo Location
`04_rsiflow/workflow_sim.py` - Workflow graph with adaptive routing

---

## 5. RSIGym: A Flexible Environment for Recursive Self-Improvement

**arXiv**: 2610.10310 (October 10, 2026)  
**Authors**: Fanqing Meng et al. (Evolvent AI, NUS)

### Core Idea
Agent-native research environment based on **Everything as a Service (EaaS)**. Exposes training, inference, rollout, evaluation, and sandbox execution through reusable services.

### Key Mechanism
1. **EaaS design**: All capabilities as reusable services
2. **Three improvement tracks**:
   - **Data track**: Improve training data
   - **Harness track**: Improve execution harness
   - **Joint track**: Optimize both together
3. **RSI-Index metric**: Mean fraction of remaining performance gap closed
4. **Budget controls**: Shared budget and permission controls

### Results
- **Opus 5**: RSI-Index = 0.4809 under $500 budget per benchmark
- **Five benchmarks**: SWE-bench Verified 17.67% → 50.33%, others improved
- **Joint track**: Outperforms data-only or harness-only

### Laptop Adaptation
⚠️ **Partial (metric demonstration only)**
- Implement RSI-Index calculation on synthetic data
- Simulate EaaS service calls as function calls
- Compare data/harness/joint tracks on toy task
- Runtime: ~3 minutes for metric calculation

### Demo Location
`05_rsigym/metric_demo.py` - RSI-Index calculation and track comparison

---

## 6. Self-Evolving Coding Agents via Harness-Policy Optimization (Self-HPO)

**arXiv**: 2610.22791 (October 18, 2026)  
**Authors**: Mingda Zhang et al. (CUHK, Fudan, UIUC, etc.)

### Core Idea
Harness and policy are mutually reinforcing—evolving only one is suboptimal. Self-HPO alternates harness and policy optimization, using the evolving policy as its own harness proposer.

### Key Mechanism
1. **H-step**: Policy analyzes failures, proposes new harness candidates
2. **P-step**: Policy updated via RL under selected harness
3. **Iterative alternation**: Harness targets policy's evolving failure modes
4. **Hard task identification**: Failures become next harness search set

### Results
- **Qwen3.5-35B-A3B**: Resolve rate 57.8% → 64.8%
- **Out-of-distribution**: Gains generalize
- **Component synergy**: Joint gain > sum of individual gains
- **Reliability**: Improved pass@1 and expanded pass@k frontier

### Laptop Adaptation
⚠️ **Partial (conceptual demo only)**
- Simulate harness as test suite, policy as simple solver
- H-step: Policy selects which tests to include
- P-step: Policy solves problems under selected tests
- Runtime: ~5 minutes for 5 alternation cycles

### Demo Location
`06_self_hpo/concept_demo.py` - Simulated harness-policy alternation

---

## 7. Terminal-RSI: Recursive Self-Improving Terminal Agents

**arXiv**: 2610.22192 (October 17, 2026)  
**Authors**: (Affiliations TBD)

### Core Idea
Alternating actor-only Recursive Self-Rewrite (RSR) with critic-inheriting Recursive Policy-Refine (RPR). Coordinates phase-local value calibration with reward evolution.

### Key Mechanism
1. **Recursive Self-Rewrite (RSR)**: Actor-only self-improvement
2. **Recursive Policy-Refine (RPR)**: Critic-inheriting refinement
3. **Phase-local value calibration**: Adapt values to policy changes
4. **Reward evolution**: Updates reward signals across cycles
5. **Fivefold actor-rate reduction**: Control exploration in second cycle

### Laptop Adaptation
❌ **Not suitable for laptop**
- Requires terminal infrastructure and complex RL setup
- Would need PPO, GAE, and asynchronous execution
- Recommended for mechanism analysis only

### Demo Location
`07_terminal_rsi/mechanism_analysis.md` - Conceptual explanation

---

## 8. R2Orch: Recursive Self-Improvement for Agent Orchestration

**arXiv**: 2610.22740 (October 18, 2026)  
**Authors**: Mingda Zhang et al. (CUHK Shenzhen, Fudan, UIUC, etc.)

### Core Idea
Recursive Self-Play Orchestration: inner loop of self-play improves orchestrator on self-chosen tasks; outer loop improves how the inner loop improves.

### Key Mechanism
1. **Inner loop**: Self-play improves orchestrator on chosen tasks
2. **Outer loop**: Improves the improvement process itself
3. **Recursive Learnability**: Reward proposer for choosing tasks with diverse outcomes
4. **Skill Withdrawal**: Remove skills when orchestrator performs well without them
5. **Skill-Internalization**: Outer loop internalizes skills into orchestrator

### Laptop Adaptation
⚠️ **Partial (toy multi-agent simulation)**
- 3-4 agents with simple skills (e.g., sorting, search)
- Self-play as skill competition on toy tasks
- Skill withdrawal as skill removal based on performance
- Runtime: ~10 minutes for 10 self-play rounds

### Demo Location
`08_r2orch/toy_orchestration.py` - Multi-agent skill competition

---

## 9. SwarmRSI: Recursive Self-Improvement through Evolving Scientific Agent Swarm

**arXiv**: 2610.20431 (October 14, 2026)  
**Authors**: (Affiliations TBD)

### Core Idea
Evolves scientific agent swarms for RSI. Combines evidence and implementations from different research directions to guide subsequent experiments.

### Key Mechanism
1. **Feedback-Guided Swarm Mutation**: Refine hypotheses and implementations using feedback from other agents
2. **Complementary Swarm Recombination**: Reuse retained hypotheses and components across agents
3. **Recursive Swarm Evolution**: Feedback loop integrates both mechanisms
4. **Experience accumulation**: Research experience improves subsequent experiments

### Results
- **OpenProblems, NatureBench, MLE-Bench Lite**: SOTA performance
- **Experience impact**: Accumulated experience improves future research

### Laptop Adaptation
⚠️ **Partial (simplified swarm simulation)**
- 5 agents with different research strategies
- Simple tasks (e.g., parameter tuning, small experiments)
- Mutation as strategy adjustment, recombination as strategy mixing
- Runtime: ~15 minutes for 10 evolution cycles

### Demo Location
`09_swarm_rsi/simplified_swarm.py` - 5-agent scientific swarm

---

## Summary Table

| Paper | Laptop Demo | Runtime | Primary Contribution |
|-------|-------------|---------|---------------------|
| Budget RSI | ✅ Full | < 5 min | Scoring edits before execution |
| SO-RSI | ✅ Full | < 2 min | Second-order diagnostic inquiry |
| AReaL-RSI | ⚠️ Partial | ~10 min | Multi-agent coordination |
| RSIFlow | ⚠️ Partial | ~5 min | Adaptive workflow orchestration |
| RSIGym | ⚠️ Partial | ~3 min | EaaS environment + RSI-Index |
| Self-HPO | ⚠️ Partial | ~5 min | Harness-policy alternation |
| Terminal-RSI | ❌ No | N/A | RSR + RPR coordination |
| R2Orch | ⚠️ Partial | ~10 min | Self-play orchestration |
| SwarmRSI | ⚠️ Partial | ~15 min | Swarm mutation + recombination |

## Laptop Demo Requirements

**Fully Executable (2 papers)**:
- Python 3.8+
- NumPy
- Standard library only
- No GPU required
- < 10 minutes total runtime

**Partial Demos (6 papers)**:
- Python 3.8+
- NumPy, NetworkX (for graphs)
- Simulated environments (toy tasks)
- No GPU required
- ~50 minutes total runtime

**Analysis Only (1 paper)**:
- Markdown documentation
- Conceptual explanations
- No code execution

---

**Last updated**: October 26, 2026
