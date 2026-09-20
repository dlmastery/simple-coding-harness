# Method checks on 20 September

These notes record selected primary-source reading. No paper implementation was reproduced. Full appendices remain outside the completed reading scope.

## HarnessDev

[Version 1, sections 3.2–3.5, 4.1, and 6.1](https://arxiv.org/html/2609.01437v1). Creation and evolution are separate stages. The executor and scorer stay fixed within a comparison; creator and executor can differ. Evolution feedback scores measure adaptation. Later withheld evaluation addresses generalization. The human references are public system results, not uniformly paired controls. One trajectory per creator/runtime cell cannot supply population uncertainty. The study leaves using an evolved harness as the next development environment to future work. Course consequence: lab 10.31 must separate generated-harness quality, builder quality, and inherited improvement machinery.

## Harness-of-Harness

[Version 1, sections 3.1–3.4](https://arxiv.org/html/2609.01481v1). The model, base harness, roles, and runtime policy stay fixed. Software artifacts and execution evidence evolve. Planning, development, and testing use separate invocations; runtime permissions enforce their different authority. Only the developer changes the artifact. Course consequence: repeated project improvement does not establish that the agent harness or its improver changed. Preserve artifact state and evidence state separately. A same-context role prompt in the classroom does not reproduce the source's enforced separation.

## S3Gym

[Version 1, sections 4–5](https://arxiv.org/html/2608.31100v1). Read the method, evaluation separation, and selected results; not every appendix. History, summary memory, and parameter training are different update paths. Self-judging estimates immediate reward under game rules. Ground-truth verifier rewards stay outside exploration feedback in the main setting. Evaluation uses disjoint seeds and is not added to the next update's data. Reported benefits vary; parameter updates can hurt. Course consequence: lab 10.32 is an adjacent external-memory exercise. It omits the games, self-judgment protocol, and actual parameter training. It cannot establish the paper's training effects.

## Additional discovery

[VideoHarness-RSI](https://arxiv.org/abs/2608.24302) first appeared 25 August; version 2 appeared 3 September. Abstract and metadata only. The authors study executable context construction around a frozen vision-language model. This is a useful optional comparison for context-management lessons. Read full methods before making stronger claims.

The date-filtered social search did not verify a new Meta/FAIR post-only result. This is an access and discovery limit, not evidence that none exists. Older results returned by the search engine were not counted as current-month releases.

## SQL-Zero

[Version 1](https://arxiv.org/html/2609.04697v1), submitted 4 September. Authors: Daniel Machado Pedrozo, Julia Soares Dollis, Bryan Lincoln Marques de Oliveira, Vinicius Alboneti Aguiar, Sávio Salvarino Teles de Oliveira, and Telma Woerle de Lima Soares; Universidade Federal de Goiás. Sections 3–6 inspected. Caveats include single training runs, unequal gold-control update budgets, unresolved paired margins, and degraded later 7B transfer. Code was not run. Teaching consequence: lab 07.07 must label its untrained role exchange as an analogy.

## Negative Self-Distillation

[Version 1](https://arxiv.org/html/2609.11699v1), sections 2–3 and the main-result table inspected. The student receives parameter updates; two teacher contexts use frozen initial weights. A generated negative condition changes one teacher's input. A probability-difference gate targets the bounded unlikelihood penalty. The reference term is evaluated at sampled tokens; do not present it as an exact full-vocabulary KL computation. The complete estimator and implementation were not audited. Course consequence: this is a weight-learning contrast for 07.03, not evidence that editing Markdown trains the coding agent or that its improvement algorithm rewrites itself. No training or reported result was reproduced.

## ADMET-EvO

[Version 2](https://arxiv.org/html/2609.10121v2), sections 2.1 and 3.1–3.4, plus selected evaluation descriptions inspected. The language model proposes actions. Deterministic components execute, judge, and update evidence; the proposer cannot redefine those verdicts. Data, feature, and model interventions are separated. Failed and inconclusive outcomes remain in the record. The expanded-task figure explicitly contains positive cases, so it cannot alone establish the success rate of all discovered tasks. Course consequence: connect endpoint meaning to ontology checks and preserve unsuccessful search history. Do not infer an inherited revision of the improvement algorithm from the title. Supplementary data, code, and full statistical claims remain unaudited.

## SafeEvolve

[Version 1](https://arxiv.org/html/2609.02786v1), selected methods 3.1–3.4 and Appendix D inspected. Bounded prompt or skill edits are checked in paired comparisons while the policy is frozen. Separate supervised and reinforcement-learning stages update policy weights. Appendix D explicitly leaves evolving the coordinating meta-strategy to future work; its current search and update schedules are fixed. Course consequence: use this as a contrast beside ScienceBuddy, separating coupled component updates from a revised improvement procedure inherited by later rounds. The entire evaluator, benchmark suite, and training implementation were not audited or reproduced. A classroom skill edit does not execute those weight updates.

These three sources were already inside the dated inventory. This pass opened their primary full texts; it did not add new discovery queries or change the paper count. Reading status now reflects the selected sections above, not a claim that every appendix has been read.
