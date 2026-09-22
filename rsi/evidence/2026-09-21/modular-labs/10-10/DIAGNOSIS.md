# The identity disappears in context compression

Both input observations contain candidate trial-001. The short trace keeps it through context preparation and reaches the stub. The long trace has candidate trial-001 at observation, then candidate=MISSING immediately after context preparation. Completion refuses missing candidate identity. This is the earliest relevant divergence.

Patch context.py only: discard the long details field while preserving candidate and duration fields. Keep the completion gate strict. Changing that gate to accept missing identity would hide the symptom and weaken the contract. The fixture driver fixes operation order; loop.py documents that order and is not a separate scheduler implementation. The unchanged driver, observation, tool stub, and completion code remain part of the comparison boundary.

These are deliberately constructed traces, not naturally observed language-model errors. The next two checks test this narrow repair on both original cases. They cannot establish general context-compression quality.
