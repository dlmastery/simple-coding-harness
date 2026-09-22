# Retained replay policy

Local-memory weight alpha: 0
Budget: eight candidate attempts
Tie rule: smaller alpha. Lookup cost is separate from any later fitting cost.

Four common broad probes precede four ranked candidates. The rank combines equal-weight experience with feature-profile proximity; it never uses a dataset name. The chosen weight minimizes mean leave-one-development-task-out normalized selection loss. Only two same-kind peers support each replay fold. This tiny pool can overfit, and the weight was itself selected on the six development outcomes. It needs new-task evaluation.

This is recorded-candidate replay, not a new reproduction of Dream-RSI's simulator or its full branching discovery process. The course's separately archived tree study tests those additional mechanisms. No new models were fitted here.
