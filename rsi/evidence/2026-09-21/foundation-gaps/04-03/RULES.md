# Three invariants

1. An input with a declared direct derivation from target must not be used as a feature.
2. A fitted transform uses train only.
3. Search must not select on final.

These are declared-fact checks, not inference about omitted facts. Unknown relation names are rejected by the supplied implementation; a separate unknown-relation case is outside this run allowance.
