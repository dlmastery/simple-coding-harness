# Swap the pointer without rerunning the experiment

This is a new deterministic replay of saved scores, not a new fit or an independent agent decision. Both procedure files are read. The active pointer is an in-memory selection; the historical workspace stays unchanged.

| Selected version | Governing partition | Retained skill |
|---|---|---|
| v1 | selection | parent |
| v0 | training | child |

Under v0, the selection-based promotion requirement disappears. The task, external MAE, data, and final evaluation do not change. Both original procedures compute training and selection scores; the changed action is which score governs retention, not whether the other score exists.
