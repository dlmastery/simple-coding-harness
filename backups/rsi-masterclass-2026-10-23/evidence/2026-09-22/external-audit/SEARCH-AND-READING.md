# Source trail, 21–22 September 2026

The local date changed during this work. Initial discovery used 22 August–21 September; refreshed discovery used 23 August–22 September. Every discovery query included explicit dates and the tool's 31-day recency filter. Search results sometimes ignored those constraints; original source dates determined inclusion.

## Exact discovery queries

```text
recursive self improvement agent harness arxiv after:2026-08-21 before:2026-09-22
self evolving agent improvement procedure September 2026 arxiv after:2026-08-21 before:2026-09-22
site:arxiv.org "EvoUndo" after:2026-08-21 before:2026-09-22
site:arxiv.org "Agentic Harness Engineering" after:2026-08-21 before:2026-09-22
"EvoUndo" code github after:2026-08-22 before:2026-09-23
site:arxiv.org "recoverability" "self-evolution" after:2026-08-22 before:2026-09-23
```

## Selection and exclusions

The broad results included existing course sources SoL-Pi and ModularRSI, a new NeoHorse-1 lead, and a secondary mention of EvoUndo. The exact-title query located the original EvoUndo arXiv record. Local inventory searches found no existing EvoUndo or NeoHorse entry. EvoUndo was selected for the unfamiliar-source exercise because its revised evaluation protocol makes a useful, bounded audit; NeoHorse remains abstract-screened only. The Agentic Harness Engineering lead resolves to an April work in the selected paper's references, so it is not counted as new-month research. Secondary summaries and social snippets were discovery aids, not technical evidence.

| Primary source | Version/date checked | Reading depth |
|---|---|---|
| [EvoUndo arXiv record](https://arxiv.org/abs/2608.28363v2) | First 28 Aug; v2 16 Sep 2026 | Identity, history and abstract checked |
| [EvoUndo v2 HTML](https://arxiv.org/html/2608.28363v2) and [PDF](https://arxiv.org/pdf/2608.28363v2) | v2 | Sections 2–4, selected results in 5–7, section 8 limits, reproducibility statement, selected D.4/F/G/J.1 passages and tables read. Other appendices not fully reviewed. |
| [EvoUndo v1 HTML](https://arxiv.org/html/2608.28363v1) | 28 Aug | Initially opened through the search lead; inspected initial formulation/method text before switching to v2. Not a full revision diff. |
| [EvoUndo repository](https://github.com/evoundo/evoundo/tree/1d4c96951557f60df9d362e90e4848dad802c40e) | Pinned commit in REPOSITORY-IDENTITY.md | README, LICENSE, package metadata and docs/benchmarks.md inspected; recursive tree listed. No implementation audit or execution. |
| [NeoHorse-1](https://arxiv.org/abs/2609.08183v1) | First/v1 8 Sep 2026 | Primary abstract and dates only; methods, affiliations, model artifacts and results unaudited |

EvoUndo authors: Tanmay Sah, Dolly Sah, Harshul Jain and Tanya Sah. The v2 front matter lists independent researchers. It is a preprint; no peer-review or institutional endorsement is inferred. The paper displays CC BY 4.0. The inspected software LICENSE identifies PolyForm Noncommercial 1.0.0; paper and software licenses are distinct. No full paper or software source is republished here.

## Access and artifact limits

One HTML follow-up returned HTTP 503, causing associated text-find requests to fail. PDF text access succeeded and supplied the remaining selected passages. Two PDF screenshot requests, for zero-based pages 6 and 23, returned internal errors. No screenshot inspection is claimed. The course's existing capstone illustration was inspected locally and retained.

The repository README identifies the paper as its research basis. Read-only API requests pinned the commit and returned 264 untruncated tree entries. REPOSITORY-READS.csv records hashes of the decoded UTF-8 response text for four inspected files; these are not byte hashes of the complete repository. The benchmark document concerns software latency/overhead. This limited inspection did not establish a mapping from that release to the paper's frozen candidate outcomes. Do not convert that gap into a claim that no artifacts exist.

Original author X posts and any full social thread were not verified in this bounded audit. No claims rely on social snippets. A useful next artifact check would identify the exact primary-cohort manifest, outcome vectors and analysis commit.
