# How this RSI course plan was developed

This log records completed actions, findings, decisions, and next steps. It is a concise process record, not a raw chat transcript. Planning date: 19 September 2026.

## Completed work

| Step | Action | Result and implication |
|---|---|---|
| 1 | Captured the user's course objective and constraints | Plan first; implementation follows review. Students use skills and natural language. |
| 2 | Cloned `dlmastery/simple-coding-harness` locally | Initial inspected revision: `eed9cbbdf19c665ae54646253f303be85030798c`. |
| 3 | Decoded the user-provided MHTML transcript locally | Used it to identify claims to check. Raw browser files remain local; a later step archives redacted text. |
| 4 | Inspected the RSI tree, README, skills, hooks, and validation discovery | Found 18 flat lesson directories, a 2,576-line README, duplicated skills, and tests tied to the old directory pattern. |
| 5 | Examined evaluation and execution claims | Identified gaps between role instructions and actual isolation, broad hook checks, and tests that check wording rather than live behavior. |
| 6 | Drafted a themed course plan | Established the progression through processes, loops, graphs, ontology, system intelligence, meta-harnesses, self-* concepts, and RSI. |
| 7 | Expanded named research sequences after user feedback | Added substantial ScientistTwo and ScienceBuddy treatment and corrected details of RSIAgent memory ownership. |
| 8 | Broadened the research search | Added procedure graphs, skill evolution, feedback design, compatibility failures, harness benchmarks, and efficiency studies. |
| 9 | Applied the user's one-month search window | Current inventory covers 20 August–19 September, with the latest two weeks prioritized. Older sources are separate. |
| 10 | Strengthened the teaching and writing requirements | Added clear run instructions, context, key takeaways, quizzes, next steps, plain technical prose, and checks for lasting understanding. |
| 11 | Revised the running task after user feedback | Replaced the provisional handbook task with regression and classification hill climbing. The ML workflow now includes the full data science process. |
| 12 | Checked primary dataset pages | Proposed small UCI Bike Sharing and Wine Quality tasks. Recorded provenance, leakage, split, and label-design issues for implementation. |
| 13 | Added a path to larger compute | Kept laptop defaults while defining compute adapters, budgets, resumption, and evaluation rules for future GPU or cluster jobs. |
| 14 | Recorded the illustration brief | Imagen 2.5 requested; white backgrounds and rich, readable technical illustration. Exact generator access remains unresolved. |
| 15 | Prepared durable planning records | Master plan, research inventory, steering/restart notes, and this work log are ready for a GitHub checkpoint. |
| 16 | Pushed and verified the first checkpoint | Commit `7f6bbd61eb029a307b38525e00beadc57d3535dc` exists on `codex/rsi-masterclass-rebuild`; the remote hash matched the local hash. |
| 17 | Added intermediate provenance | Saved search notes, claim corrections, source hashes, a redacted transcript, the redaction script, and an artifact index. Recorded missing earlier drafts and extraction-command history as gaps. |
| 18 | Created the reusable course-building skill | Full instructions, five references, and agent metadata are versioned under `skills/build-research-codelabs/`. A coverage table maps all user guidance. |
| 19 | Validated the skill and documentation | The skill validator passed after supplying its missing PyYAML dependency. The link checker found a validation file that had not yet been written; the record was added for the next check. |
| 20 | Rechecked links and installed the skill | All 85 local links across 17 Markdown files resolved. All seven installed skill files matched repository hashes; the installed package passed the validator. |
| 21 | Checked the redacted source | Output hash matched the manifest. No email addresses or original forwarded-message identifiers remained under the applied checks. |
| 22 | Pushed the complete skill and provenance checkpoint | Commit `6ae9a411d7dec732debb0293f9817350bc08dc11` was pushed; the remote hash matched local HEAD and the working tree was clean. |

## Why the plan changed

**The course needed missing conceptual steps.** The existing structure introduces machinery before students have a reason to use it. The plan adds explicit transitions and small experiments that expose the need for each mechanism.

**The research search was initially too narrow.** It relied too much on the source transcript and existing course. The wider search uses mechanism families and primary-source dates. Eight new advanced experiments cover distinct ideas that the first plan missed.

**The main task must serve an AI/ML class.** The user rejected a document-handbook example as the central project. Small supervised learning tasks preserve laptop access while making feature search, model search, error analysis, and research improvement meaningful.

**Small demonstrations should not prevent larger work.** The laptop route controls cost and teaching complexity. The compute adapter separates those choices from the research method so students can later run harder jobs without rewriting the conceptual design.

**Visual and writing quality are requirements.** Each lesson needs a clear explanation and a diagram that shows the mechanism. The plan records a concrete editorial and visual review process rather than treating polish as a final decoration pass.

## Evidence and limits

The repository inspection supports the findings in the master plan. It does not establish that every current lab was executed or that every defect has been found.

The research inventory distinguishes metadata checks from method inspection. No selected paper has been reproduced here. The raw source remains local; its redacted text derivative is archived with a clear unverified-source notice. Implementation began on 20 September; the dated entry below supersedes the initial planning-only status.

An original X post returned HTTP 403. The linked official benchmark page was accessible. No new Meta/FAIR post-only result in the target month was verified in this pass. These limits are recorded in the inventory.

## Checkpoint procedure

Planning records belong in `how-did-i-generate-it/rsi/`. Use a dedicated working branch. For each meaningful milestone:

1. Update the plan, requirements, and work log where the decision changes them.
2. Inspect the changed files and check links, counts, and status claims.
3. Commit a coherent set of changes with a descriptive message.
4. Push the working branch to GitHub.
5. Compare the local and remote commit hashes before reporting the backup as complete.

Implementation checkpoints should include relevant runtime evidence and failures. Keep expensive or private artifacts out of Git; record their locations and checksums where appropriate. Never commit secrets or the private transcript.

## Next steps

1. The user authorized implementation by saying “continue.” Preserve the complete reusable skill already installed and on GitHub.
2. Continue implementation from the dated record below.
3. Build representative onboarding, ML loop, ontology, and recursion lessons before expanding the pattern.
4. Validate the laptop path and the declared agent adapters. Record actual resource use.
5. Produce and inspect the requested illustrations after generator access is resolved.
6. Continue through the full course, updating this log and checkpointing progress.

## 20 September: working foundation

Created a small shared experiment tool and seven canonical course skills. Downloaded original UCI bike and wine archives, retained attribution, and pinned source hashes. Verified actual bike row count and wine duplicate groups. The runtime trains preprocessing only on training rows, excludes leakage features, keeps failed attempts, locks final evaluation, and stops on contract changes.

Eight new behavioral tests passed. The previous course's offline suites passed; 19 live checks were skipped. Five actual CPU fits and two data inspections produced retained reports, predictions, timings, and charts in `rsi/evidence/2026-09-20/`. The linear bike candidate outperformed the tested tree candidate; no guaranteed improvement is implied. Total agent cost and peak memory were not measured.

The student lesson layer and complete theme expansion remain in progress. Requested illustration model access is unresolved; a user question is pending. Measured data charts are separate from that illustration requirement. A research refresh found MetaRSI and HarnessEvolve; methods still need review.

## 20 September: complete authored sequence

Published 101 labs with individual briefs, prompts, checks, counterexamples, takeaways, and four-question explained quizzes. All 12 themes have entry pages; 38 research labs have 13 subdirectory indexes. Added MetaRSI and HarnessEvolve after inspecting relevant primary methods and comparisons. Reading-depth limits remain recorded.

Rebuilt the walkthrough and added start, glossary, instructor, research, adapter, and migration pages. Replaced flat packs while preserving Git history. Updated test discovery. Eleven shared tests passed, including 21 mechanism checks. All 1,248 local links resolved. Seven learner skills passed validation. These are publication and component checks, not 101 completed learner runs.

Foundation commit `3dc2e5dbcaee0686fee766e19dc169638ee056dc` was pushed and its remote hash verified. The next checkpoint preserves the complete authored sequence before deeper walkthrough and illustration work.

## 20 September: controlled execution and inherited procedure

Verified that the complete authored-sequence checkpoint `eae0bf49ba7a3519e8e9a50cb87fa1402c77a4d1` is on the remote branch. The user asked whether periodic check-ins were occurring; confirmed the remote and prepared the next coherent checkpoint.

Ran nine additional model fits, a final refit, domain checks, and post-final refusal. Saved predictions, error slices, timings, source procedures, and failures. Added a result checker with four tests for valid evidence, a false summary, incorrect row identity, and altered target values. The full shared suite passed 15 tests; publication checks passed for 101 lessons.

Read the retained improver v1 and generated a driver that executes its required check in a new author-guided round. A labelled report copy claiming MAE 9.0 was rejected; a genuine MAE 99.175924 result was retained against the fixed 109.807668 incumbent. The trace records the selected procedure hash and actual command outcomes. No independent v0 agent was run, and no autonomous RSI advantage is claimed.

Next: tighten research adaptation labels and reading-depth records, extend compute guidance, and continue clean-start and editorial validation. Illustration provider choice remains unresolved.

## 20 September: research, portability, and visual explanations

The controlled-walkthrough checkpoint `93d3760a14a9940df23e26bc67bdf7cb22e30933` was pushed and the remote hash matched. Subsequent work added explicit activity labels for source audits, numerical examples, replay, simulations, and mechanism exercises. Corrected Harness-of-Harness: its agent configuration stays fixed while software and evidence evolve. Updated three papers' reading depth and added VideoHarness-RSI as an abstract-checked optional lead. The month inventory now has 26 papers and five reports; no new Meta/FAIR post-only result was verified.

Added a larger-compute guide, readable job brief, adapter contract, and backend acceptance checks. GPU and cluster execution remain untested. Generated and executed a concrete two-attempt bike harness from a prose brief: one valid baseline, one leakage refusal, and an exhausted-budget refusal. Preserved its package, source brief, driver, ledger, and outputs.

Exported the pushed source and ran its 15 tests. Then created a fresh Python environment from the documented requirements and passed the same tests. Recorded a clean-source baseline and checked its predictions. This is Windows setup evidence, not universal agent portability.

Authored 101 technical diagrams, rendered all, inspected representative images, and revised wide layouts. Retained both galleries and their rendered outputs. Added worked examples at important conceptual transitions and corrected the general median explanation. Prepared ten detailed raster illustration prompts; the named Imagen generator remains unavailable through the exposed selector. Technical schematics are an explicit companion, not a claimed provider substitution.

Updated the reusable authoring skill with lessons on concrete compute handoffs, accurate activity types, and diagram validation. The canonical package remains in the repository; its local installed copy is synchronized only after checking for divergence.

## 20 September: check the published reading experience

Pushed `fef74315d8de205be050a527dc1b04e8dfe5ba0e` and verified the remote hash. Inspected actual GitHub pages, including a diagram, the course map, and an explained-answer disclosure. The quiz disclosure worked. A narrow viewport exposed a too-wide introductory diagram; GitHub dark mode exposed a nonwhite live-Mermaid canvas in the overview. Retained a third first-lab diagram revision and rendered the overview as a static white image. The [visual record](visuals/REVIEW.md) states the exact scope and screenshot-retention limit.

## 20 September: isolate and verify course compatibility

Pushed the display corrections as `112805fa040086724ba31844d83491eead573292` and verified the remote hash. The user again asked about periodic check-ins; the branch was clean and GitHub held all three recent checkpoints.

Inspection found failures in the repository-wide workflow. The latest completed Linux job passed all 15 RSI behavior tests but failed in other course sections. Added a dedicated RSI workflow for clean Python 3.12 installs on Linux, macOS, and Windows. It keeps all three platform results, checks generated-page consistency, and does not change or suppress the broader workflow. Remote results remain pending until the next push.

Pushed `eceeeab64aa37206355f6b840b28c4d30c938c3f` and verified the remote hash. Its dedicated RSI run passed on all three operating systems. Archived exact environments and selected logs. The prior aggregate failure families were also verified in the planning-only checkpoint's public job log. Kept those issues separate from RSI support claims.

## 20 September: test organization and clarify self-play

Rechecked the revised overview on published GitHub in dark mode and the first lesson at phone width. Both targeted corrections displayed as intended. Closed the review tab and reset the viewport.

Ran eight small scheduling simulations for labs 07.05 and 07.06. Retained every input and event trace. The examples show dynamic dispatch losing under extra overhead and clustered work increasing urgent-job lateness. The randomized-history control still clustered, so the interpretation explicitly avoids claiming that accurate memory uniquely caused the pattern.

A focused, month-filtered search supported a self-play terminology correction. Read selected SQL-Zero methods, comparison details, and limitations. Labelled the existing proposer–critic activity as an interaction analogy without training. Updated its diagram, quiz, glossary entry, and the reusable skill's RSI preset. The source inventory now has 27 papers and five reports; three other returned titles remain unreviewed leads. No additional paper reproduction or native agent execution is claimed.

## 20 September: follow the main path from a clean workspace

Checkpoint `75e998848730c268849f67514e249a186bad86da` was pushed and verified; its dedicated three-platform CI passed. The user approved the next execution pass. Cloned that checkpoint from GitHub into a new directory and installed a fresh environment. Read the student entry and skills. Recorded the route and its same-context limitations before execution.

Ran the foundation and structure stages: 17 total ML fits, 38 foundation child commands, and 25 graph/domain checks. Saved every result, expected refusal, input copy, source hash, and process-restart checkpoint. Copied 257 generated files into evidence and verified every copy. Inspected the rendered data chart and labelled dependency graph.

The pass found a misleading shared budget display. Added persistent lesson limits and a contract checksum to the shared runner, with a subprocess regression test. Sixteen tests passed. The original journey clone stays fixed so its existing contracts remain valid. The next stage is generated harnesses, followed by a bounded old/new improver comparison; learner participation and independent contexts remain untested.

## 20 September: complete the selected author route

Pushed and verified `e22f63c6122956829bd7f7fc150b331480c65ac8`. Its dedicated RSI workflow passed on Linux, macOS, and Windows. Generated and executed separate bike and wine harness packages from readable briefs. Fourteen child commands covered five fits and the actual leakage, wrong-task, candidate-identity, and budget refusals. Recreated baseline prediction bytes matched.

Recorded a comparison protocol before generating two synthetic ML tasks. Both improvers received the same parent, fixed child proposal, task data, and two fits per case. The revised rule reads selection scores instead of training scores when promoting a task-skill edit. Eight fits completed. The revised gate rejected an overfit regression tree; both gates retained a useful classification tree. Saved all four decisions before final scoring. Retained exact procedures, data, models, predictions, costs, rejected edits, and command logs. This is a constructed same-context teaching comparison, not autonomous RSI or a general performance claim.

Completed the frozen bike final evaluation and checked all 4,376 prediction identities and targets. A post-final fit was refused. The author already knew the public task's earlier final outcome, which is disclosed. The selected route totals 31 fits, including the final refit. Copied and hash-checked all 446 learner-workspace files. Rendered and inspected the measured-result chart. Added its concrete teaching example to 09.05 and clarified the existing-workspace requirement in 08.02.

The selected route is complete. Full 101-lab activity execution, repeated recursive generations, deeper outstanding paper reviews, requested raster illustrations, native agent/backend checks, and actual student validation remain open. Keep these distinct from the completed runtime and publication checks.

## 20 September: make the original course backup explicit

Checkpoint `b501baae1b21a8fa596400f9fcd8b3b76f2ab5bf` was pushed and its remote hash matched. The user asked whether the README rewrite had started and required preserving the old version. Confirmed that the rewritten README was already pushed and that the original existed in Git at `eed9cbb` before the rewrite. Extracted an exact original README and a complete original tracked RSI ZIP into `backups/`. Verified the README Git blob and the copy inside the ZIP. The archive has 718 entries and is 1,075,588 bytes.

Recorded the actual timing: the Git snapshot predates the rewrite; the explicit backup files were created now. Added this requirement to steering and the reusable provenance skill. Opened the current README in the Codex panel for review. Further edits must preserve the backups.

The standalone original is stored as unchanged Markdown bytes with a `.txt` extension, so historical relative links are not mistaken for current navigation. The ZIP retains the original `README.md` filename and surrounding directory. A local Git attribute disables newline conversion for the standalone copy. All seven installed skill files match the canonical package; skill validation passed.

The backup checkpoint `85ceecc4e8a0609c53ff23c542df399072404449` was pushed and verified. Continued the active research audit: inspected selected primary methods for Negative Self-Distillation, ADMET-EvO, and SafeEvolve, all already inside the month inventory. Updated reading depth and concise method notes. Added the three as optional contrasts in the research guide. No paper reproduction or new lab is claimed; the count remains 27 papers and five reports. The dedicated RSI workflow for the completed journey checkpoint `b501baa` passed.

## 20 September: continue under the full completion goal

The user activated the goal to finish all original themes and tasks and every README. Read the actual checkout, skill requirements, course source, and current goal. Added a completion ledger that preserves the entire scope and separates achieved backups from partial editorial, execution, research, and visual evidence. The previous turn made concrete progress; no goal blocker is declared while further work is available.

Reviewed the first 26 labs through ontology engineering. Added individually authored worked examples, named output checks, practical recovery, and relevant quiz hints. Preserved existing measured examples and labelled invented numbers. Corrected the optional/required verification-fit contradiction in 01.03. The publisher now removes excess blank lines, and the new coverage audit checks that authored guidance reaches the README without pretending that presence proves quality.

Expanded the main walkthrough with the four distinct objects and linked a six-block path through all 101 lessons. The current inventory shows 26 labs with the new support and 37 with worked examples. Remaining ranges are explicit. All 101 pages regenerate, and publication checks passed for 1,820 links before the final ledger/index additions. No new model execution or learner validation is inferred from this editorial pass. Added CI checks for the coverage inventory and generated-page agreement.

Pushed and verified `181a599ca49a4ed4619789477cea489334ff265f`; its dedicated three-platform checks passed. Continued through system intelligence and meta-harness engineering: teaching support now covers 37 labs, with 46 worked examples. Corrected several scope/budget ambiguities and the exact-duplicate wine grouping explanation. All 1,825 local links passed. The next substantive mechanism gap is 07.07: its current role-exchange analogy does not execute learning. Add a tiny tabular self-play task with frozen evaluation and actual parameter updates before treating that teaching requirement as satisfied.
