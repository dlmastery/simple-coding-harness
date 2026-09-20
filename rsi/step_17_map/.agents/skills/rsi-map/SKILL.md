---
name: rsi-map
description: "Print the map of the rsi series - the ladder of rungs with lessons 00-16 placed, every recorded learning curve on the same curriculum side by side, the file-and-approver table, the terminology, and every external number marked reported - from the runs that exist, with a helper you build from the contract in tools.md. Use in rsi/step_17_map."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
---
# The map: you recognise the nouns because you built the toy

Run the helper through the Bash tool from this lesson's directory. You change nothing and run no
lesson: the map reads what the other lessons left under `../step_NN_*/runs/`.

## Boot order
1. This file. 2. `tools.md`. 3. `ladder.md`: the rungs, the lessons on them, the file-and-approver table, the six terms and the reported numbers - the text the helper prints around the curves.

## Procedure
1. Build `map` under `runs/rsi-map/helpers/` if it is not there yet.
2. `map --lessons ..`: the helper prints the ladder from `ladder.md`, then, for every lesson directory that has `runs/<pack>/curve.json`, its curve row (per problem, memory arm minus control arm, best val score) and its exam line (`wins` out of 5, `mean_test_gap`) side by side; a lesson without a curve is printed as `not run yet`, never invented; then the file-and-approver table, the six terms, and the numbers quoted from elsewhere, each marked *reported* with its source.
3. Answer in text with the table as the helper printed it, then one paragraph: which lessons have a recorded curve, which do not, and the one sentence the series ends on - genuine RSI by the paper's bar is not reached here, and the map says so. Stop.

## Rules
- Print the numbers the helper prints; every external number is *reported*, none is measured here.
- Do not run a lesson's curriculum to fill a gap in the table: say it is not run yet.

## Off switch
None: the map reads and prints.

## Done when
`map` answered and the table was shown.
