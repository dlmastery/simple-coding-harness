# Implementation record

## 20 September 2026: begin the rebuild

The user said “continue” after the saved plan and reusable skill checkpoint. Implementation is authorized. Starting commit: `2d0263541a50890150fe8eb04bfef7a018248e91`; branch: `codex/rsi-masterclass-rebuild`.

The first implementation slice covers onboarding, data inspection, a measured regression experiment, a bounded loop, domain rules, and the distinction between changing a solver and changing its improver. These activities test the course design before the full sequence expands.

The existing course remains in Git history. Replace its entry point and flat layout only with explicit navigation and a migration record. Other repository course series are outside this change.

### Execution design

- Students give the coding agent plain-language prompts. Canonical Markdown skills guide the session. The agent runs or generates implementation code.
- A small shared tool supplies repeatable data checks and CPU experiments. Its command line is an agent interface, not a student prerequisite.
- Freeze task, split, metric, data hash, and budget in each generated workspace. Keep individual candidates and failures. Refuse an incompatible contract rather than silently changing the comparison.
- A supplied local evaluator establishes repeatable scoring. Because the coding agent can read local files, it does not establish a secret test boundary. The course must say this before any held-out performance claim.
- Later student-authored skills decide what experiment to propose. An inherited improver must be read and used in a later round. A fixed list of models is ordinary search, not RSI.
- The runtime generates reports and measured plots. Images that explain mechanisms use the requested generator once its availability is resolved.

### Checks before expansion

Check data checksums and row counts; train-only transforms; exclusion of count components; chronological split; candidate identity; failed attempts; budget exhaustion; frozen contracts; final evaluation lock; clean-start instructions; local links; retained artifacts; and skill loading. Then run representative experiments and inspect their actual reports.

Measure Python and package versions and local execution time. Keep agent-provider costs marked unavailable when no measurement exists. Do not label GPU, cluster, or other coding-agent paths tested without a run.

### Open image decision

An asynchronous question asks whether the user accepts the available image generator or requires access to the exact requested model. The exposed tool has no Imagen model selector. Google's [Imagen documentation](https://ai.google.dev/gemini-api/docs/imagen), checked 20 September and updated 17 September 2026, says Imagen is no longer available through the Gemini API and points to Nano Banana. This does not establish availability through every other service. Do not claim to have used Imagen 2.5.

### Research refresh

Discovery now covers 20 August–20 September 2026. Two additional leads need method review: [MetaRSI](https://arxiv.org/abs/2609.06396), first submitted 6 September, revised 9 September; and [HarnessEvolve](https://arxiv.org/abs/2609.00829), submitted 1 September. Their abstracts and dates have been checked. They are not yet validated course methods or reproduced results.

## Themed lesson checkpoint

The authored sequence now contains 101 labs in 12 main themes. The research studio has 38 labs in 13 subdirectories. MetaRSI and HarnessEvolve add two dedicated mechanisms beyond the initial blueprint. The publisher and complete authored prose modules are retained under `scripts`; student READMEs contain plain-language prompts.

Replaced the large RSI README with a walkthrough, start page, glossary, and instructor guide. Retired the flat legacy packs through Git; the migration guide links their historical commit. Updated root test and snippet discovery. Other course series are unchanged apart from the RSI entry in the repository map.

The shared runner passes 11 tests, including 21 executed synthetic mechanism checks for graph order, joins, bounded repair, dependency invalidation, replay coverage, grouped rewards, and typed write boundaries. Navigation passes for all 101 lessons and 1,248 local targets. Seven learner skills pass validation. These checks do not establish completion of all learner prompts or independent-context RSI experiments.

Relevant MetaRSI mechanism and comparison sections and HarnessEvolve reference, diagnosis, gate, and selected experiment sections were inspected. Full appendices and code reproduction remain incomplete. Research notes preserve these limits.

Next: execute controlled ML walkthroughs and a representative inherited-improver exercise, retaining artifacts and failures. Review prerequisite and budget consistency. Resolve the requested image generator, inspect illustrations, and validate agent entry paths. Do not call the course finished from written coverage and component tests alone.

## Controlled execution checkpoint

The controlled ML and author-guided inherited-procedure walkthroughs above are now executed. Their drivers are retained in `scripts/run-foundation-walkthrough.py` and `scripts/run-inheritance-walkthrough.py`. Results are linked from the dated evidence index. The result checker has four meaningful failure/acceptance tests; the full shared suite passes 15 tests.

Remaining work includes research adaptation labels and reading status, compute extensions, illustrations, clean-start activity coverage, editorial review, and agent/backend validation. The inherited-procedure trace is deliberately limited to a selected procedure in one authoring context. It is not a matched autonomous improver experiment.
