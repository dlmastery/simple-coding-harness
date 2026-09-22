# Inspect the two saved attempts

Attempt one recorded begin, filter forest, select A. Its visible states never contain a candidate detail warning. Warning inspected before selection: no.

Attempt two recorded begin, filter forest, details A, details B, select B. The third visible-state file contains A's ineligibility warning; the next contains B's eligible scope. Both precede the selected-candidate state. Warning inspected before selection: yes.

This additional-change audit reads existing traces only. It adds no browser attempt. The warning existed in the frozen page before both attempts; it was not inserted after the first failure.
