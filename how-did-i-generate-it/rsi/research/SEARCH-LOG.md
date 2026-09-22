# Research search log

**22 September broad refresh:** [nine exact dated queries and result decisions](2026-09-22-SEARCH-RECORD.md) extend discovery across mechanisms, frontier labs, arXiv and original social announcements. [Selected-method reading](2026-09-22-WIDE-REFRESH.md) adds four papers to existing comparisons, bringing the retained count to 37 papers and five reports. Recently crawled older material is excluded; social-post coverage remains explicitly incomplete.

**21–22 September capstone discovery:** six explicit dated queries found EvoUndo and NeoHorse-1. The local date rollover moved the final window to 23 August–22 September. Exact queries, exclusions, versions, repository identity and HTML/PDF-image access failures are in the [source trail](../../../rsi/evidence/2026-09-22/external-audit/SEARCH-AND-READING.md). Earlier cutoff statements below are historical records.

Cutoff: 19 September 2026. Current discovery window: 20 August–19 September. Earlier searching focused on the user-supplied papers and the latest two weeks. The user then requested a broader one-month sweep.

## Queries used in the broader sweep

These query bodies were sent with `after:2026-08-19 before:2026-09-20` and the available 31-day recency filter. The date terms belong to the query, not to an assumption that the engine will obey them.

```text
"recursive self-improvement"
"self-evolving" "agents"
"harness" "co-evolution"
site:arxiv.org "harness"
site:arxiv.org "skill evolution"
site:arxiv.org "self-improving" "benchmark"
site:arxiv.org "scientific agents"
site:ai.meta.com "self" "improvement"
site:x.com "Meta" "harness"
site:x.com "recursive" "improvement"
site:deepmind.google "research" "agents"
"Harness Updating Is Not Harness Benefit"
"Library Drift" agents skills
"RSI-Index"
"AI" "research" "Kirgis"
"self-improvement" "September" "2026" site:x.com
"RSIAgent" site:x.com
"Dream-RSI"
"self-evolving" "2608"
site:microsoft.com/en-us/research "self-improvement"
site:research.google "WikiSkill"
"self-improving" "September 2026" "Meta"
"agent" "meta-harness" "September 2026"
```

A date-filtered search for the user's named writing standard, ASD-STE100, was also attempted. Its official site was then opened directly. Stable standards and dataset pages are reference checks; they are not counted as current-month AI research.

## Search before the one-month instruction

The initial broadening used queries for self-improving and self-evolving agents in September 2026, harness and skill evolution with `2609`, autonomous scientific agents, model–harness co-evolution, and evaluation benchmarks. Exact output from every earlier search is not archived. The verified source inventory records the sources retained. Do not present this file as a complete raw tool transcript.

## Screening decisions

- Open the arXiv abstract page to check the title and first-submission date.
- Read relevant full-text sections for sources likely to change the plan.
- Follow official project and repository links where useful.
- Exclude older material from the recent list even if the search engine returned it.
- Retain essential older foundations in a separate list.
- Use third-party pages only to find a primary source.

The filtered search returned older work including HyperAgents, Library Drift, a July AI-research evaluation, and older Microsoft and DeepMind pages. Their recent crawl dates did not qualify them as new research.

## Primary-source follow-up

The [research inventory](../RSI-RESEARCH-SWEEP.md) gives stable links and reading depth for retained sources. Full-text inspection focused on mechanisms, split design, feedback ownership, costs, reported failures, and the limits of recursion claims. Published figures were not reproduced in this phase.

The direct X request for `https://x.com/ValsAI/status/2098170083466191086` returned HTTP 403. The official Vals benchmark page was accessible. No contents or date from the blocked post were accepted as verified.

No raw website dump is checked in. These original notes, source URLs, source dates, and the inventory preserve the useful research record without republishing entire copyrighted pages.

## 20 September follow-up

All following discovery queries used the available 31-day recency filter. The explicit range was 20 August through 20 September. Exact query bodies:

```text
("recursive self-improvement" OR "harness evolution") after:2026-08-20 before:2026-09-21 site:arxiv.org
("self-improving" OR "recursive self improvement") after:2026-08-20 before:2026-09-21 (site:ai.meta.com OR site:research.google OR site:deepmind.google OR site:anthropic.com OR site:openai.com)
("HarnessOpt-Bench" OR "Evo-Bench" OR "SEAGym" OR "Harness-R1") after:2026-08-20 before:2026-09-21
("recursive self-improvement" OR "harness" OR "self-improving") ("FAIR" OR "Meta") site:x.com after:2026-08-20 before:2026-09-21
("recursive self-improvement" OR "self-improving agents") site:x.com ("Meta" OR "FAIR") after:2026-08-20 before:2026-09-21
"SEAGym" site:arxiv.org after:2026-08-20 before:2026-09-21
"Harness-R1" site:arxiv.org after:2026-08-20 before:2026-09-21
```

VideoHarness-RSI was new to the inventory; its primary abstract and version history confirmed eligibility. Other results included already recorded papers, an older May webinar, and undated or older leads. They were not counted as new releases. The final three-query batch returned no search results. That is not evidence of absence.

Direct primary-page follow-up inspected HarnessDev, Harness-of-Harness, and S3Gym as recorded in [method notes](2026-09-20-METHOD-NOTES.md). Direct opens are source checks, not unfiltered discovery queries.

## Self-play terminology check

The following discovery query used the 31-day filter:

```text
self-play proposer solver agents reinforcement learning after:2026-08-20 before:2026-09-21 site:arxiv.org
```

It returned SQL-Zero (2609.04697), LURE (2608.21871), TIPCODER (2609.03309), and a searchless-chess study (2608.27757). Only SQL-Zero received direct metadata and method checks in this pass. The other three remain unreviewed leads and do not enter the source count. The purpose was to correct a role-exchange analogy in lab 07.07, not to add another required exercise.

## Later 20 September refresh

All three queries used the 31-day recency filter as well as the explicit window:

```text
("recursive self-improvement" OR "self-evolving" OR "harness evolution") after:2026-08-20 before:2026-09-21 site:arxiv.org
("self-improvement" OR "self-evolving" OR "recursive") ("agents" OR "harness") after:2026-08-20 before:2026-09-21 (site:research.google OR site:deepmind.google OR site:ai.meta.com OR site:microsoft.com/en-us/research)
("recursive self-improvement" OR "self-improving agent" OR "harness evolution") (Meta OR FAIR OR Google) site:x.com after:2026-08-20 before:2026-09-21
```

New primary checks confirmed EvoHarnessBench (3 September, v2 10 September), Ecdysis (10 September), and OpsHarness (26 August). Selected methods were inspected and added to the dated notes. The inventory is now 30 papers and five reports. SkillForge and ForeDreamer received deeper selected-method reading without changing that count.

The lab-domain query also returned recently crawled Microsoft profile pages describing older work, including SkillOpt. Those pages were not counted as recent research releases. A skill-harness embodied-agent title remains a lead until its exact primary date and method are verified. The X query supplied no new verified original post in this batch; the Meta/FAIR social coverage gap remains explicit. This refresh is not an exhaustive survey.

## 21 September refresh

All discovery queries used a 31-day recency filter and explicit date bounds:

```text
("recursive self-improvement" OR "harness evolution" OR "self-evolving agents") site:arxiv.org after:2026-08-21 before:2026-09-22
("recursive self-improvement" OR "self-evolving" OR "harness") (site:research.google OR site:deepmind.google OR site:ai.meta.com OR site:microsoft.com/en-us/research OR site:openai.com OR site:anthropic.com) after:2026-08-21 before:2026-09-22
("recursive self-improvement" OR "self-improving agents" OR "harness evolution") (Meta OR FAIR OR Google) site:x.com after:2026-08-21 before:2026-09-22
```

Repeated results included ScienceBuddy, ModularRSI, EvoHarnessBench, and Ecdysis. Followed Microsoft's SHAPER and OEO publication links to arXiv version histories. SHAPER has a 10 September revision of an 11 August first submission; record that distinction. OEO is dated 10 August with no listed revision and is excluded from current-window additions. Sico remains undated. Older SkillOpt and PURER pages and recently crawled profile pages were not counted as new research.

No new original Meta/FAIR social post was verified. The absence of a verified result does not establish that no such announcement exists.

Direct full-text follow-up inspected selected sections of VideoHarness-RSI, Recursive Criticality, and SHAPER. [Reading notes](2026-09-21-METHOD-NOTES.md) record scope and teaching consequences. The corpus now retains 31 papers and five reports, with older-first/recent-revision work explicitly separated. No new mandatory lab or paper reproduction is claimed.
