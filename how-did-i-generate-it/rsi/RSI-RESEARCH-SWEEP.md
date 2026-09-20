# Research for the RSI course

Current inventory after the later 20 September refresh: **30 papers and five reports**. New primary-source checks added [EvoHarnessBench](https://arxiv.org/abs/2609.04280) (3 September; v2 10 September), [Ecdysis](https://arxiv.org/abs/2609.11677) (10 September), and [OpsHarness](https://arxiv.org/abs/2608.25661) (26 August). Selected methods were inspected; full evaluations and implementations remain unaudited. They enter existing comparison exercises rather than adding redundant required labs. The [method notes](research/2026-09-20-METHOD-NOTES.md) and [search log](research/SEARCH-LOG.md) record sections, dates, and limits. Earlier counts below are historical checkpoints.

## 20 September refresh

The discovery window now extends through 20 September 2026. Two additions bring the current-month inventory from 23 to 25 papers, alongside five reports. [MetaRSI / RSI2](https://arxiv.org/abs/2609.06396) first appeared 6 September, with v2 on 9 September. [HarnessEvolve](https://arxiv.org/abs/2609.00829) appeared 1 September. Relevant mechanism and selected experiment sections were inspected; full appendices and code were not reproduced.

MetaRSI adds composition across data, harness, and model surfaces and a revised scheduling policy. Its reported per-term gains decline despite increasing cumulative gains. HarnessEvolve adds checked answer-conditioned reference paths and quality/performance gates. Neither is independently reproduced here. Both now have dedicated classroom exercises.

A further date-filtered sweep added [VideoHarness-RSI](https://arxiv.org/abs/2608.24302), first submitted 25 August and revised 3 September. Its abstract and version history were checked; full methods remain unread. The current count is 26 papers and five reports. This addition is an optional context-construction lead, not another claimed reproduction or a reason to expand the required lab count.

HarnessDev methods, selected evaluation details, and limitations were inspected. Harness-of-Harness fixed/mutable components, role boundaries, and cross-loop state were inspected. S3Gym exploration, judging, memory, training, evaluation separation, and selected results were inspected. The [dated notes](research/2026-09-20-METHOD-NOTES.md) record the limits and teaching consequences.

The remainder preserves the original 19 September sweep. Reading-depth cells for those three sources have been updated; its original counts describe that earlier sweep.

A focused self-play terminology check then added [SQL-Zero](https://arxiv.org/abs/2609.04697), submitted 4 September. Selected methods and limitations were inspected. It informs a correction to lab 07.07 without adding a lab. The current inventory is **27 papers and five reports**; earlier counts above record earlier checkpoints.

Research window: **20 August–19 September 2026**. Priority window: **6–19 September 2026**. This inventory contains 23 papers and five lab or benchmark reports from that month. Earlier foundations are listed separately.

The first reading list was too narrow. The broader sweep adds work on procedure graphs, skill libraries, feedback design, model–harness compatibility, efficiency, and failed improvement. These additions change the proposed experiments, not just the bibliography.

This is a source inventory for course planning. “Methods inspected” means relevant full-text sections were read. It does not mean every appendix was audited or the experiment was reproduced. No paper's code has been executed as part of this sweep.

## How the search was done

Searches cover recursive improvement, harness generation and evolution, agent memory, skill evolution, autonomous science, model–harness co-evolution, evaluation, and research costs. Sources include arXiv, official lab pages, author projects, repositories, and original researcher posts.

All discovery queries after the user's date instruction include `after:2026-08-19 before:2026-09-20` and the available 31-day recency filter. Query families include:

- Recursive self-improvement and self-evolving agents.
- Harness evolution, meta-harnesses, and model–harness co-evolution.
- Skill evolution, persistent memory, and procedure graphs.
- Scientific agents, research benchmarks, and negative transfer.
- Official Google, DeepMind, OpenAI, Anthropic, Meta, and Microsoft research.
- Original X posts naming RSI, Dream-RSI, RSIAgent, or agent harnesses.

Search engines returned some old results despite the filters. Dates in the tables below come from the primary source. A crawl date, repost date, or bibliography update does not count as a new research release. Sources discovered before the one-month instruction were reclassified by their actual publication dates.

The sweep follows relevant links from papers to methods, appendices, official projects, and code. Third-party summaries serve only as discovery leads. Technical descriptions below use primary sources. This is broad coverage of the selected mechanisms, not a claim to have found every relevant paper.

## Papers from the latest two weeks

Dates are first submissions unless a revision is also shown. All dates are in 2026.

| Date | Primary source | Why it belongs | Reading status |
|---|---|---|---|
| 17 Sep | [SoL-Pi: Recursively Scaling Auto-Research Loops for Efficient Agent Harness](https://arxiv.org/abs/2609.20519) | Harness efficiency under fixed quality checks; useful limits on the recursion claim | Methods and limitations inspected |
| 17 Sep | [ScientistTwo: Pioneering the Human Knowledge Frontier with Autonomous AI](https://arxiv.org/abs/2609.19644) | Hypotheses, experiments, ablations, review, and successive research results | Methods and evaluation inspected |
| 15 Sep | [Reflect, Revise, Reuse: Training-Free Skill Evolution for GUI Agents](https://arxiv.org/abs/2609.17653) | Targeted skill edits and separate critic context | Methods, selected ablations, and critic limitations inspected |
| 15 Sep | [ScienceBuddy: Recursive-in-Recursive Self-Improvement for Interactive Scientific Agents](https://arxiv.org/abs/2609.17523) | Human feedback and coupled harness/model updates | Methods, evaluation, and selected appendix details inspected |
| 14 Sep | [The Economics of Recursive Self-Improvement](https://arxiv.org/abs/2609.15802) | Resource limits and feedback assumptions | Relevant theoretical discussion inspected |
| 14 Sep | [RSIAgent: Autonomous Exploration for Recursive Self-improvement in New Environments](https://arxiv.org/abs/2609.15364) | Exploration, outcome checks, and persistent experience | Methods and memory protocol inspected |
| 14 Sep | [Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858) | Search-policy changes through replay of discovery trees | Methods, project page, and repository status inspected |
| 14 Sep | [ModularRSI](https://arxiv.org/abs/2609.14857) | Restricted changes to harness components | Methods and repository structure inspected |
| 10 Sep; v2 15 Sep | [The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement](https://arxiv.org/abs/2609.11873) | Definitions, autonomy, inheritance, and strength of evidence | Framework and relevant v2 sections inspected |
| 10 Sep | [Negative Self-Distillation: Learning to Reason by Avoiding Flaws](https://arxiv.org/abs/2609.11699) | A distinct form of model self-training; useful for the self-* comparison | Selected methods, setup, and main-result table inspected 20 Sep |
| 9 Sep; v2 10 Sep | [ADMET-EvO: a self-evolving scientific agent for sustained research across heterogeneous tasks](https://arxiv.org/abs/2609.10121) | Evidence-guided experiment selection and retention of inconclusive results | Relevant method and selected evaluation sections inspected 20 Sep |
| 8 Sep | [Procedural Graphs: Self-Evolving Execution Structures for LLM Agents](https://arxiv.org/abs/2609.09153) | Editable procedure structure; connects early graph lessons with later evolution | Methods, split design, and selected results inspected |
| 8 Sep | [Co-Evolving Harnesses and Models: On-Policy Correction Helps Weaker Models Catch Up Where Imitation Fails](https://arxiv.org/abs/2609.09134) | An explicit counterexample to assuming two improvements will combine | Methods, experiments, and affiliation inspected |
| 8 Sep | [Environments as Scaffold: Enriching Feedback to Bootstrap Self-Evolving Agents in Long-Horizon Tasks](https://arxiv.org/abs/2609.08404) | The content and timing of feedback can change what an agent learns | Feedback design and training/evaluation setup inspected |

## Other papers within the month

| Date | Primary source | Why it belongs | Reading status |
|---|---|---|---|
| 2 Sep | [SafeEvolve: Harness-Policy Co-Evolution from Agent Experience for Safety Alignment](https://arxiv.org/abs/2609.02786) | A comparison case for bounded harness edits and model adaptation | Selected methods and Appendix D scope inspected 20 Sep |
| 1 Sep | [HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?](https://arxiv.org/abs/2609.01437) | Tests harness creation, subsequent evolution, cost, and transfer | Methods, selected evaluation, and limitations inspected 20 Sep |
| 1 Sep | [Harness-of-Harness: Multi-Day Autonomous Software Development with Continual Improvement](https://arxiv.org/abs/2609.01481) | Fixed agent configuration develops software through separated roles | Methods and state/permission boundaries inspected 20 Sep |
| 31 Aug | [S3Gym: Can LLMs Turn Self-Testing and Self-Judging into Self-Improvement?](https://arxiv.org/abs/2608.31100) | Compares history, memory, and training; reports uneven gains and negative transfer | Methods, evaluation separation, and selected results inspected 20 Sep |
| 31 Aug | [Recursive Criticality of AI Self-Improvement](https://arxiv.org/abs/2609.00137) | A theoretical account of amplification and increasing research difficulty | Abstract and metadata checked |
| 27 Aug | [WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution](https://arxiv.org/abs/2608.27454) | Separates raw experience, accumulated knowledge, and executable skills | Architecture, update rules, and selected ablations inspected |
| 25 Aug | [SkillForge: Evolving Verifiable Skills for Reinforcement Learning Agents](https://arxiv.org/abs/2608.24747) | Skills require continued verification rather than endless accumulation | Selected methods 3.1–3.3 inspected 20 Sep |
| 25 Aug | [Recuris](https://arxiv.org/abs/2608.24876) | Working state and reusable experience have different roles | Relevant mechanism inspected |
| 21 Aug; v2 24 Aug | [ForeDreamer: A Self-Evolving Dual-Agent Memory Architecture for Future Event Prediction](https://arxiv.org/abs/2608.20920) | Distinguishes current factual evidence from experience across tasks | Selected architecture and method sections inspected 20 Sep |

## Lab reports and announcements

These are different types of evidence. A company's account of internal work is not an independent reproduction. A theory or forecast is not an experimental result.

| Date or update | Primary source | Course use |
|---|---|---|
| 6 Sep | [Research acceleration: The view inside OpenAI](https://openai.com/index/research-acceleration-view-inside-openai/) | Examine internal research-assistance measurements and their limits |
| 6 Sep | [An Alien Mind](https://openai.com/index/an-alien-mind/) | Separate a frontier lab's expectations from demonstrated mechanisms |
| Listed 17 Sep | [Measurements for understanding the pace of AI development inside frontier labs](https://www.anthropic.com/institute/measuring-pace-of-ai-development) | Distinguish automation, oversight, compute, and scientific progress |
| Update 18 Sep; original date unresolved | [When AI builds itself](https://www.anthropic.com/institute/recursive-self-improvement) | Compare internal observations with claims about future recursion |
| Updated 18 Sep | [Vals RSI Index](https://www.vals.ai/benchmarks/rsi_index) | Read an R&D benchmark's task definitions, reference scores, costs, and limits |

Google work found in the sweep includes Procedural Graphs, WikiSkill, Dream-RSI, and ScientistTwo. The model–harness compatibility study identifies Salesforce AI as its affiliation. Institution labels will follow the paper's author list rather than assumptions based on names or social posts.

X is included in the search. A direct request for a [Vals AI post](https://x.com/ValsAI/status/2098170083466191086) returned HTTP 403. The official benchmark page was accessible. The post's full contents and date are not treated as verified. No new Meta/FAIR post-only result within this window was verified in this pass. This is a coverage gap, not evidence that no such work exists.

The Meta search returned [HyperAgents](https://ai.meta.com/research/publications/hyperagents/), dated 24 March. It belongs in the earlier lineage, not the recent list. Microsoft and DeepMind searches also returned older pages. They were excluded from the current-month count. Further social-source work must verify author identity, date, the complete relevant thread, and any linked evidence before a claim enters a lesson.

## What changes in the course

The main project is CPU-based regression and classification. These papers supply mechanisms and comparisons. They do not turn the course into a sequence of expensive benchmark reproductions. The eight added advanced labs address distinct ideas.

| Lab | Addition | Laptop activity | What the activity does not establish |
|---|---|---|---|
| 10.27 | WikiSkill | Retain traces and a knowledge notebook while accepting or rejecting ML research skills | That every larger skill library improves performance |
| 10.28 | Procedural Graphs | Edit a small experiment workflow after comparing successful and failed runs | That a procedure graph is an ontology or a better recursive improver |
| 10.29 | EvoSkill-GUI | Revise a skill for a local experiment-results page with a separate critic | Results on the paper's full GUI benchmarks |
| 10.30 | SoL-Pi | Test a few harness changes for total research cost under fixed quality rules | Sustained recursive acceleration |
| 10.31 | HarnessDev and Harness-of-Harness | Generate a small ML harness, improve it, and try it on another task | Universal transfer across models or coding agents |
| 10.32 | S3Gym | Compare raw history with summarized memory using a tiny text environment | Automatic improvement from accumulating experience |
| 10.33 | Environments as Scaffold | Compare procedural hints with more informative observations, then remove help | The weight-training results of the source paper |
| 10.34 | Model–harness fit | Run a small compatibility experiment and audit the published training comparison | That a prompt-level demonstration reproduces model training |

The already planned sequences for Dream-RSI, RSIAgent, ModularRSI, AIDE², ScientistTwo, and ScienceBuddy remain. SkillForge, SafeEvolve, ForeDreamer, ADMET-EvO, and Negative Self-Distillation enter relevant comparison or reading exercises. A new paper gets a new lab only when it adds an idea students need to build or test.

Three findings deserve careful explanation:

**Efficiency and recursion need different evidence.** SoL-Pi uses fixed capability tolerances before accepting efficiency gains. Its limitations describe reusing a cheaper harness to improve its successor as future work. The course must preserve that distinction. [Methods and limitations](https://arxiv.org/html/2609.20519v1).

**Useful knowledge and active instructions need not have the same lifecycle.** WikiSkill retains the wiki when a skill proposal is rejected. Its inference agent has restricted access to that wiki during evolution. The classroom design must not collapse all three stores into one long prompt. [Architecture and update rules](https://arxiv.org/html/2608.27454v1).

**A stronger component can make the combined system worse.** The Salesforce study reports that full-trajectory imitation harms models under their evolved harnesses. It studies corrections at states visited by the weaker model as an alternative. This belongs beside ScienceBuddy to prevent the assumption that harness gains and weight gains always add. [Study](https://arxiv.org/html/2609.09134v1).

Other useful checks are already recorded in the master plan: automated peer-review ratings in ScientistTwo; distinct feedback sources in ScienceBuddy; actor-owned memory in RSIAgent; and the limits of replay coverage in Dream-RSI. Claims in those papers must remain separate from outcomes measured in class.

## Earlier foundations

These sources are retained because they explain lineage or were explicitly requested. They do not count as developments from the past month. Do not spend new discovery searches on old work while recent coverage remains incomplete.

| Source | Date | Reason to retain |
|---|---|---|
| [AIDE²](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement) | 14 Jul 2026 | Explicit user requirement; nested research and a separate ignition test |
| [MetaSkill-Evolve](https://arxiv.org/abs/2607.05297) | 6 Jul 2026 | Task skills and the procedure that improves them |
| [HyperAgents](https://ai.meta.com/research/publications/hyperagents/) | 24 Mar 2026 | Editable task and meta-agent mechanisms |

STOP and DGM can appear as brief historical links after their primary sources are checked for the specific claims used. They must not displace the recent studies. Stable small datasets are teaching fixtures, not claims about recent research.

## Work still needed before publishing lessons

- Read methods, appendices, evaluation protocols, and limitations for entries checked only at abstract level.
- Check releases, licenses, dependency sizes, data access, and reproducibility for each selected implementation.
- Verify more original researcher posts, especially Meta/FAIR sources that search indexing may miss.
- Keep full paper reproduction separate from small mechanism exercises and result audits.
- Test every required exercise on a declared laptop. Test larger compute adapters where hardware is available and mark the rest untested.
- Refresh the same one-month search window relative to the delivery date. Record new submissions, revisions, corrections, and exclusions.

The inventory is ready to guide the plan. It is not evidence that the course or any paper reproduction is complete.
