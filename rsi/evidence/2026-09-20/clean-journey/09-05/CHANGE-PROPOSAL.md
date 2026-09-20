# Revise the promotion procedure

The synthetic diagnostic below has perfect training fit but worse selection MAE. The old acceptance rule would promote it. Change only the promotion partition from training to selection. Expected effect: reject an overfit child while allowing a child that improves selection. Risk: a noisy small selection set can reject useful edits or favor another overfit choice. A later final regression would challenge the usefulness of this gate. Both procedures and the external evaluator remain frozen during the comparison.

This revision is author-guided and selected using declared numerical fixtures, not discovered autonomously. Fresh synthetic ML cases are generated only after the fixture checks.
