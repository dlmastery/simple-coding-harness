# Discovery record for the broad 22 September refresh

The web tool was used for all searches and primary-page reading. Each discovery query had explicit dates and a recency filter. Direct opens and clicks checked sources found by those queries; they were not new undated discovery searches. The tool often returned older material despite the filters, so eligibility was checked on primary version histories.

| Query | Recency | Domain filter in addition to query |
|---|---:|---|
| `"recursive self-improvement" after:2026-08-22 before:2026-09-23` | 31 days | None |
| `"self improving" "harness" after:2026-08-22 before:2026-09-23` | 31 days | arxiv.org |
| `"self improvement" research after:2026-08-22 before:2026-09-23` | 31 days | deepmind.google, research.google, openai.com, anthropic.com |
| `"recursive" "self" after:2026-08-22 before:2026-09-23` | 31 days | ai.meta.com, microsoft.com, x.com |
| `site:anthropic.com research development "26%" after:2026-08-22 before:2026-09-23` | 31 days | None |
| `site:arxiv.org "self-improvement" "2026" after:2026-09-08 before:2026-09-23` | 15 days | None |
| `"self-improvement" after:2026-08-22 before:2026-09-23 site:x.com (FAIR OR Meta OR Google)` | 31 days | None |
| `"harness" after:2026-08-22 before:2026-09-23 site:microsoft.com/en-us/research` | 31 days | None |
| `("recursive self-improvement" OR "harness evolution") after:2026-08-22 before:2026-09-23 (site:deepmind.google OR site:research.google OR site:openai.com OR site:ai.meta.com)` | 31 days | None |

## Results that changed the course

- [Harness tampering](https://arxiv.org/abs/2609.00069v1): metadata says 30 August, despite its September identifier. Added selected-method reading.
- [Metaⁿ](https://arxiv.org/abs/2608.24735v1): 25 August. Added a fixed-operator comparison and checked the author's repository README.
- [SIFT](https://arxiv.org/abs/2609.19526v1): 17 September. Added selected methods, evaluation and limitations.
- [AutoSaddler](https://arxiv.org/abs/2608.23041v1): 24 August. Followed Microsoft's publication link; added selected methods and protocol reading.
- [Anthropic measurement report](https://www.anthropic.com/institute/measuring-pace-of-ai-development): already present. Clarified what its automation statistic measures.

[Reading notes](2026-09-22-WIDE-REFRESH.md) preserve the scope and course mapping. Existing results included the framework paper, Dream-RSI, MetaRSI and Economics of RSI; they were not counted twice. News, glossary pages and social commentary were discovery context only, not technical evidence.

## Exclusions and access limits

- Google's [self-evolving recommendation study](https://arxiv.org/abs/2602.10226v3) first appeared 10 February and was last revised 2 August. Its upcoming RecSys date and recent crawl do not make it a new release in this window.
- Microsoft results included May's HarnessAudit, April's M-star, June's retrospective harness optimization, July's OpenForgeRL page and the 20 August Agent Lightning announcement. None was added as a new current-window paper in this pass; later revisions were not established here.
- OpenAI's 2017 evolution-strategies page and Google's older robotics/RL posts were returned by the date-filtered search and excluded.
- No new original Meta/FAIR X post was verified. Search output is not evidence that such posts do not exist. The prior Vals-post access failure remains unresolved; this pass did not claim to reopen it successfully.
- SIFT and harness-tampering code releases were not verified. AutoSaddler advertises a code link, but it was not inspected. Only Metaⁿ's top-level README and repository identity were checked; no new paper implementation was run.

This is a bounded refresh, not an exhaustive literature census. Exact browser/tool outputs remain in the authoring session; the repository retains this query/result index rather than wholesale copies of third-party pages.
