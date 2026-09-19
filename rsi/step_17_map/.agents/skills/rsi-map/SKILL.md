---
name: rsi-map
description: Print the map of the rsi series - the ladder of rungs with lessons 00-16 placed, every recorded learning curve on the same curriculum side by side, the file-and-approver table, the terminology, and every external number marked reported - from the runs that exist. Use in rsi/step_17_map.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The map: you recognise the nouns because you built the toy

Run every command through the Bash tool from this lesson's directory. You
change nothing and run no lesson: the map reads what the other lessons left.

## Procedure
1. `python ../tools/map.py --lessons ..`
   The script prints the ladder (rung, lessons, the decision the system takes, what stays human), the learning curves side by side (from each lesson's `runs/<pack>/curve.json`; a lesson not run yet is named as such, never invented), the file-and-approver table, the six terms, and the numbers quoted from elsewhere - each marked *reported* with its source.
2. Answer in text with the `table` as the script printed it, then one paragraph: which lessons have a recorded curve, which do not, and the one sentence the series ends on - genuine RSI by the paper's bar is not reached here, and the map says so. Stop.

## Rules
- Print the numbers the script prints; every external number is *reported*, none is measured here.
- Do not run a lesson's curriculum to fill a gap in the table: say it is not run yet.

## Done when
`map.py` answered and the table was shown.
