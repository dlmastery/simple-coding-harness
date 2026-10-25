# Fixed rules

A prediction recipe cannot use a feature derived from the target. Fitted transforms use training rows only. Search selects on selection data, never final data. Valid example: model uses hr. Invalid example: model uses a renamed total_users field that is declared target-derived. The alias does not change its meaning.
