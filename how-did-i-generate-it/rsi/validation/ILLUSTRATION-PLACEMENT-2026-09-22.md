# Check illustrations where readers encounter them

The user asked whether all remaining illustrations were linked in their
respective pages and whether the presentation was linked from the README.
This audit reads the actual Markdown pages and confirms selected embedded
image paths resolve. It does not merely count files in the asset folder.

**338 placement checks pass:** 101 individual lesson infographics, 101 precise
step diagrams, 101 matching gallery entries, 12 whole-course theme maps,
13 research-group figures, four RSI entry-page figures, the repository
entry-page mindmap, two expanded studio/capstone maps, two results-guide
conceptual figures and its measured nested-study chart.

A separate check of the published commit bd7f70c4 found 382 local image embeds
across 572 course Markdown pages and no missing tracked targets. This broader
check includes the parent harness course and excludes evidence/assets pages.
The new measured chart is covered by the 338-placement working-tree check
and the next evidence publication; it was not present in that earlier commit.

One omission was found: the studio's opening research-reading group had no
overview figure. The first audit attempt stopped on its absent figure mapping.
Added the existing lab 10.02 announcement-evidence illustration and reading
guidance to the canonical research-group source, then regenerated the pages.
The next audit passed every placement. No image generation was required.

Both READMEs now link to the [presentation status](../../../rsi/PRESENTATION.md).
The 37-slide storyboard and draft notes are available; no RSI PPTX exists yet.
The eventual deck remains conditional on the experimental repair, method
comparisons and presentation review. A different-topic PPTX in the repository
is not the requested RSI presentation.

See [the checked rows](ILLUSTRATION-PLACEMENT-2026-09-22.csv) and
[the audit source](../scripts/check-illustration-placement.mjs). Rejected and
superseded generated images remain in provenance rather than being inserted
into lessons. This check establishes coverage and valid paths; it is not a
fresh visual review of all 101 rendered lessons.
