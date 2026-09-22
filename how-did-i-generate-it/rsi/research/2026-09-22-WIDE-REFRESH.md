# Research refresh on 22 September

Discovery window: 23 August–22 September 2026. Priority: 9–22 September. This adds four papers to the retained inventory, bringing it to **37 papers and five reports**. Older foundations remain separate. Each entry below names the sections actually inspected; none is a full-paper review or reproduction. [Queries and exclusions](2026-09-22-SEARCH-RECORD.md) make the coverage boundary explicit.

## Harness tampering

[Auditing Harness Tampering in Self-Improving Agents, v1](https://arxiv.org/html/2609.00069v1), Xing Wang, Xiaoyi Zhang and Jie Shao, UESTC; [submitted 30 August](https://arxiv.org/abs/2609.00069v1). Read taxonomy, dataset construction, evaluation protocol and Tables 2–3. The audit separates where an edit acts from which obligation it breaks. Seeded benign/tampered pairs test the auditor; findings on released trajectories are auditor judgments, not direct ground-truth labels. Paper: CC BY 4.0. Supplementary materials and runnable artifacts were not inspected. Classroom connection: classify an old report reused for a new candidate as a provenance failure; do not infer intent from the failure.

## Metaⁿ

[Metaⁿ, v1](https://arxiv.org/html/2608.24735v1), Zae Myung Kim, Young-Jun Lee, Seungyeon Jwa and Dongyeop Kang; Minnesota and Seoul National University; [submitted 25 August](https://arxiv.org/abs/2608.24735v1). Read sections 2.1–2.2, 3.4 and limitations. Its operator stays fixed while generated wrappers and their accumulated inputs change. Its depth convention is author-defined. Deeper layers can regress; more layers alone do not prove improvement. Paper: CC BY-NC-ND 4.0. The [repository](https://github.com/minnesotanlp/meta-n/tree/b7081843d3c7b0e0f418ca10aaf2ccbff856e7f8) lists MIT licensing and calls its results exploratory. Inspected the live README; GitHub API resolved this revision. Implementation, dependencies and runs remain unaudited. Compare this architecture with an explicitly revised improver in 10.37.

## SIFT

[Self Improvement via Fast Tree-search, v1](https://arxiv.org/html/2609.19526v1), Xinghong Fu, Aravinth Kulanthaivelu and Yutaro Yamada; MIT and Sakana AI; [submitted 17 September](https://arxiv.org/abs/2609.19526v1). Read methods, cost accounting, Polyglot setup and limitations. Pairwise patch judgments are aggregated with a Bradley–Terry model to guide search while task evaluations continue. The judge does not receive benchmark outcomes. Downstream execution still validates gains; the stronger judge and one-dimensional ranking limit interpretation. Paper: CC BY 4.0. No runnable release was verified. Compare screening cost with confirmation cost in 10.30; do not replace measured quality with a judge preference.

## AutoSaddler

[AutoSaddler, v1](https://arxiv.org/html/2608.23041v1), Sungho Park and twelve co-authors; Microsoft, KAIST, SUSTech and POSTECH; [submitted 24 August](https://arxiv.org/abs/2608.23041v1). Read section 4, experiment split protocol and Appendix R. The process diagnoses traces, makes restricted edits, checks the same batch, and uses development results for selection. Reflection retains fixed and regressed cases. Final feedback does not drive another update. This supervised setup assumes task outcomes; its training analogy does not make textual edits numerical gradients. Paper: CC BY 4.0. Code is linked by the authors but was not inspected or executed. Use it as a comparison in 10.31.

## Frontier-lab measurement

Revisited Anthropic's [measurement report](https://www.anthropic.com/institute/measuring-pace-of-ai-development), already counted among the five reports. Read the automation section and methodological appendix. Its August snapshot reports 26% of R&D at the supervised AI-led level and no measured subset at full autonomy. The index uses a frozen task basket and person-time weighting; model judges introduce uncertainty. Those measurements do not by themselves establish a faster recursively improving system. The earlier inventory lists 17 September; this page retrieval exposed no publication date, so this pass does not independently reconfirm that date. Internal data and independent replication remain unavailable here.

## Teaching decisions

These readings sharpen existing questions in 10.02, 10.30, 10.31, 10.36 and 10.37. They do not add model fits, mandatory labs or a new illustration requirement. The 101-lab progression and its existing conceptual figures remain intact. The next section of each affected README still leads through the same teaching sequence. Source-system scores are not substituted for local results.

No full source paper, third-party figure, or repository implementation is copied into the course. This record preserves citations, versions, reading scope and short original summaries. Original social-post coverage remains incomplete; a bounded search cannot establish absence.
