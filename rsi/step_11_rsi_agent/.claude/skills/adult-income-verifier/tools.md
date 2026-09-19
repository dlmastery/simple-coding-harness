# Tools

## Allowed
- read_traces - the fit rows of this problem: recipe, val_score, error, and the profile; --tally adds the pairwise count
- write_card - merge cards into the actor pack's memory.json, validated against memory.schema.json

## Forbidden
- fit_recipe, score_test, save_model, load_splits - the verifier never fits and never touches the test split
- read_memory - the cards are in the actor pack's memory.json, which write_card merges into
