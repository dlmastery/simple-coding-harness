# Separate exposure condition

## Read 10-27/ACTIVE-SKILL.md

# Choose an eligible ML recipe

Seconds per second: 1
Seconds per millisecond: 0.001
Seconds per minute: 60
Seconds per microsecond: 0.000001
Unknown units: refuse

Choose lower selection MAE first. Break equal-MAE ties with shorter converted duration. Convert known duration units using the factors above. Refuse a comparison containing a unit without a declared conversion. Break remaining ties by candidate ID. Input quality scores and durations come from the same declared comparison contract. A missing conversion must not be invented from the raw number.

## Read 10-27/NOTEBOOK.md

# Retained knowledge

The prior unknown-unit identity fallback selected a candidate from uninterpretable duration metadata. Source: raw/RESULT.md and raw/CONVERSIONS.csv. Scope: the constructed ticks case, not every possible unit convention. Preserve an explicit conversion contract or refuse this comparison. This note is knowledge for the improver, not an automatically promoted task instruction.

The new two-case check repeated that weakness: the proposal passed the seconds case but selected A where the ticks case required refusal. Sources: check-seconds/RESULT.md, check-unknown/RESULT.md, and CHECKS.csv. The gate rejected the proposal and kept the accepted refusal-capable skill. Retain this scoped observation even though the proposed procedure is not promoted. NOTEBOOK-v0.md preserves the notebook before this addition.
