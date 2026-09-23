# Presentation publication review

Reviewed 22 September 2026. Current artifact: **rsi-masterclass-review-v2.pptx**.
SHA-256: b7557350d9b49d4d74fe2981bdf9dae0e53af9e25d8825b34b601cd0ec2cc0a1.

## Content and appearance

All 37 final-file renders were inspected at 1280 × 720. The review covered
complete images, readable labels, arrow direction, clipping, chart values,
table text and the distinction between conceptual examples and measured results.
Slides 1–16 and 18–37 retain the first draft's inspected renders byte for byte.
Slide 17 originally used an ontology figure that did not fit its explanation.
Version 2 uses the existing 09.01 solver–improver–evaluator diagram. Its final
render was inspected separately. No course illustration was regenerated.

The deck uses 33 existing figures and four native chart/table slides. Dense
research maps work as narrated overviews; the linked codelabs provide the
full-size versions for independent reading. The editable chart contains actual
attempt counts. The comparison table includes all four controls and uncertainty.

The finalizer passes package, font and geometry checks. A separate checker
passes 120 checks: every slide has its complete authored notes and source URL,
the native chart and workbook exist, chart values match the archived attempt
ledger, and comparison-table values match the frozen contrasts. Thirty-six
renders are identical to version 1; only the corrected slide 17 changed.

## Preserved failures and publication fixes

The initial builder could not discover runtime fonts until its bundled runtime
path was set. The failed source and startup log remain in build-v1. The first
content-checker draft assumed relative notes targets and a fixed chart directory.
The package uses absolute notes targets and a chart under ppt/slides/charts.
Those checker assumptions were corrected without changing the deck. The initial
checker source remains in build-v2.

The first navigation check also found that storyboard copies retained paths
relative to their former parent directory, and that local dependency junctions
exposed third-party documentation to the scan. The original storyboard bytes
are retained with a .original suffix. Readable copies use pinned absolute
repository links. Temporary dependency junctions were removed after rendering.

## Limits

The later [native PowerPoint review](NATIVE-REVIEW.md) verifies read-only
opening, all notes, native object recognition and slide export in PowerPoint 16.0.
Other applications, slideshow controls and learner feedback on pacing remain untested. The draft reports measured search savings and mixed
prediction outcomes, with no claim of a reliable overall RSI gain. Preparing
this review draft does not imply that the user approved final framing or that
the broader course execution goal is complete.

## Course navigation checks

After adding the download and notes links: 101 RSI lessons and 6,233 local
links pass with no publication problems. All 338 expected illustration
placements pass. The parent harness checker also passes: 54 lessons, 69 pages,
899 local links and 1,396 unchanged implementation/configuration files.
Selected current figures belong in the teaching pages; superseded illustration
versions remain in provenance. No missing selected placement was found.
