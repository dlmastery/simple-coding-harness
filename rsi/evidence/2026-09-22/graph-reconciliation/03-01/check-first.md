# Ordering verdict

Order: frame → inspect → split → check → fit → report

Edges: [('frame', 'inspect'), ('inspect', 'split'), ('split', 'fit'), ('fit', 'check'), ('check', 'report')]

Violations: ['fit -> check']

REFUSED: predecessor occurs after its dependent action.
