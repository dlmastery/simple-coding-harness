# Presentation sources and review

The [current PowerPoint review draft](output/rsi-masterclass-review-v2.pptx)
contains 37 slides with embedded notes. Read the [course introduction](../../../rsi/PRESENTATION.md),
[speaker notes](build-v2/SPEAKER-NOTES.md) or [rendered slides](RENDERED-SLIDES.md).

| Artifact | Purpose |
|---|---|
| [Teaching outline](STORYBOARD.md) | Sequence, teaching points and evidence boundaries |
| [Builder](build-v2/create-deck.mjs) | Artifact-tool authoring source |
| [Source manifest](build-v2/SOURCE-MANIFEST.json) | Asset hashes and pinned course sources |
| [Build input, as executed](build-v2/STORYBOARD-SOURCE.md.original) | Exact historical input bytes |
| [Readable build input](build-v2/STORYBOARD-SOURCE.md) | Same snapshot with repository links made absolute |
| [Package checks](build-v2/FINALIZATION.json) | Structure, fonts, geometry and native objects |
| [Content checks](build-v2/CONTENT-CHECKS.json) | Notes, result values and unchanged slide renders |
| [Content checker](check-published-deck.py) | Read-only checks against archived result CSVs |
| [Review record](REVIEW.md) | Visual inspection, corrections and limitations |
| [Native PowerPoint review](NATIVE-REVIEW.md) | Read-only opening, all notes, native objects and exported slides |
| [Earlier PowerPoint draft](output/rsi-masterclass-review-v1.pptx) | Retained intermediate version |
| [Earlier builder and renders](build-v1/) | First build, startup failure and original review material |

The build uses the bundled presentation runtime. Its local dependency junctions
are temporary and are not committed. Each build's candidate PPTX, exported PPTX,
rendered slides, layout records, source manifest and notes are retained.
The original storyboard copies retain the historical “not built” status they
had when used as inputs; that text does not describe the current deliverable.
Readable copies use absolute links to the same pinned source revision. The
builder accepts either copy because these links resolve to identical citations.

The slides are a review draft, not user approval of final presentation framing.
No new model fits or image-generation calls were required for publication.
