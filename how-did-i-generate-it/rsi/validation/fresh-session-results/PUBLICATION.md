# Publication checks

Checked locally on 23 September 2026 after both child sessions ended:

- Independent handoff audit: 13,115 assertions passed; zero audit fits.
- Archive: all 58 child files match their original SHA-256 identities and
  their staged Git blobs. Binary treatment preserves original text bytes too.
- Course navigation: 101 lessons, 6,317 local links, zero publication problems.
- Selected illustration placement: 338 checks, zero failures.
- Lesson publisher and activity inventory regenerated from canonical sources.
- Teaching support and worked examples: 101 of 101 each.
- Staged whitespace check passed.

No runtime tool code changed. The actual one-fit execution and its checker
cover this handoff change; the full model suite was not rerun locally.
The branch's RSI workflow performs its usual runtime and publication checks
on push. Do not assume that remote run passed before its result is inspected.

The Start here page now links the illustrated course map, complete visual
guide, presentation and speaker notes. The root and RSI READMEs already link
the 37-slide PPTX and notes directly. No infographic or slide was regenerated.
