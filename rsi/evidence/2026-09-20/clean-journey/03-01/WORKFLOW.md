# Action dependencies

Each edge names the result required by its destination. The diagram source is workflow.mmd. This sequence has no cycle; the later bounded repair graph does.

- frame: needs task request.
- inspect: needs frame.
- split: needs inspect.
- fit: needs split.
- check: needs fit.
- report: needs check.
