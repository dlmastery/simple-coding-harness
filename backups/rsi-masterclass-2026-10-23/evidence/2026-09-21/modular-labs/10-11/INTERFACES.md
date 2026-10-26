# Before execution

| Version | Context produces | Completion consumes |
|---|---|---|
| Base | candidate, duration_value, duration_unit | candidate and either explicit units/value or duration_seconds |
| A | candidate, duration_seconds | same as base |
| B | same as base | candidate, duration_value, required duration_unit |
| A+B | same as A | same as B |

A removes the unit field that B requires. Both may pass alone while the combination refuses. Original: 2 seconds. Fresh: 0.5 minutes, equivalent to 30 seconds. Malformed: candidate missing. All fixtures were authored before this comparison and visible to the author; fresh is not blinded. The fit stub is reachable only after completion validates the interface. These are illustrative components, not the source paper implementation.
