# The ladder, the files, the terms, the reported numbers

## The ladder (arXiv:2609.11873, section 3): which decision moved from the designer to the system

| Rung | Lessons | The decision the system takes | What stays human |
|---|---|---|---|
| L1 precondition | 00 intent | none | what to improve, how, success |
| not RSI (B0 / AutoML / harness engineering) | 01 regular, 02 loop, 04 graph | none: a fixed procedure | everything |
| L1 | 03, 05, 08 (the writers) | executes a generation procedure | the intent, the acceptance (approve / edit / reject) |
| L4 | 06 RSI harness, 07 proof, 09 (approval: human), 11 RSIAgent, 13 Recuris | revises persistent state (cards, plan, skill cards) from run feedback | the verifier contract, the schema, the off switch |
| L2 | 10 Dream-RSI | chooses the search strategy from replay | the policy library |
| L2 -> L5 flavour | 12 ModularRSI | patches one harness module off-benchmark | the module boundaries, the pool |
| L4 -> L5 flavour | 09 (approval: gate), 14 DGM lineage, 15 AIDE2 | revises the improver's policy line / its own source / its operators behind a protected evaluator | the archive rule, the gate, the meter, the task set |
| L5 | 16 MetaSkill-Evolve | revises its own meta-skills on a slow clock | the clock, the human yes on every meta change |

## The file-and-approver table: what changed, and who said yes

| Lesson | The file that changed | Who approved |
|---|---|---|
| 01, 02, 04 | nothing | - |
| 03, 05, 08 | a whole pack, landed | the human (approve / edit / reject) |
| 06, 07 | memory.json | the verifier contract (human-written), no per-card approval |
| 09 human | SKILL.md policy line, schema.json forbid, memory.json | the human, per patch |
| 09 gate, 10, 16 fast loop | the same three | the private gate |
| 11 | plan.json, memory.json | the planner's rule; the verifier |
| 12 | one modules/*.md of the loser | the private gate, on the pool |
| 13 | one skill-memory card | the tally (validated), one per visit |
| 14 | SKILL.md + loop.json (the actor's source) | the gate, then the human |
| 15 | operators.md | the meter, across the set |
| 16 slow loop | one roles/*.md of the meta pack | the human, every k problems |

## Six terms

- self-refine: a better answer this turn, no persistent change (B0) - lessons 01-05 are at most this.
- learning: persistent state revised from feedback under an acceptance rule (L4) - lesson 06 on.
- self-organise / emergence: structure nobody wrote - not in this series; every file here was written by a human or by a rule a human wrote.
- AutoML: a fixed search over a fixed space - lesson 01 is exactly this.
- bounded RSI: the improver revises the harness behind a protected evaluator, with a human archive rule and gate - lessons 09 gate, 14, 15, 16: L5 flavour.
- genuine RSI (the paper's bar): closed loops with persistence, transferred and attributed autonomy, verified inheritance under matched budgets, domain-appropriate feedback infrastructure - not reached here, and the map says so.

## Reported numbers (none measured here)

- Headroom-Closed Index: advanced mathematics 86.4, graduate science 85.8, software engineering 52.6, search / terminal agents 56.8, tool agents 39.9 - reported, arXiv:2609.11873.
- Goedel Agent lost ground in 14 % of trials - reported, arXiv:2609.11873 (Challenge 1).
- DGM raised SWE-bench 20 -> 50 % with a human-fixed archive and parent selection - reported, arXiv:2505.22954 via 2609.11873.
- A-Evolve-Training 0.80 -> 0.86 over four rounds - reported, arXiv:2609.11873.
- AIDE2: seven successive improved versions in 100 outer steps, 16x context compression - reported, Weco AI tech report (July 2026), unverified.
- Recuris: +32.2 on the longest tasks - reported, arXiv:2608.24876.
- ModularRSI, RSIAgent, Dream-RSI, MetaSkill-Evolve: the tutorial's specific numbers (162x, 71.97 -> 78.98, 47.57 -> 52.43) are not in the abstracts and stay reported.
