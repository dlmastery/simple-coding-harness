# Diagram and portability checkpoint

Date: 20 September 2026.

| Check | Actual result |
|---|---|
| Mermaid CLI 11.17.0, first gallery | 101 diagrams rendered without parse errors |
| Mermaid CLI 11.17.0, revised gallery | 101 diagrams rendered without parse errors |
| Static diagram publisher | 101 PNGs copied with dimensions, source index, and SHA-256 manifest |
| Lesson publisher | 101 READMEs and briefs generated in 12 themes |
| Local Markdown target check | 1,587 targets resolved before this record and final index additions |
| Generated harness driver | Baseline checked, leakage refused, two-attempt limit enforced |
| Fresh exported source, fresh Python environment | 15 tests passed; setup details in CLEAN-SOURCE-CHECK.md |
| Reusable skill validator | Passed with Python UTF-8 mode |
| Updated learner scale skill validator | Passed |
| Canonical versus installed authoring skill | All seven files matched by SHA-256 after synchronization |
| Git whitespace check | Passed |

The first authoring-skill validator invocation used the Windows default cp1252 decoder and failed on Unicode punctuation. Running the same validator with `python -X utf8` passed. This was an encoding failure in the validator invocation, not an omitted skill instruction.

The [visual review](../visuals/REVIEW.md) identifies the images actually inspected and the layout revision. Rendering all diagrams does not prove independent semantic review of every image. Native other-agent execution, GPU/cluster runs, and teaching effectiveness remain untested.
