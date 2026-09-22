# Ordering verdict

Order: frame → split → inspect → fit → check → report

Edges: [('frame', 'inspect'), ('inspect', 'split'), ('split', 'fit'), ('fit', 'check'), ('check', 'report')]

Violations: ['inspect -> split']

REFUSED: predecessor occurs after its dependent action.
