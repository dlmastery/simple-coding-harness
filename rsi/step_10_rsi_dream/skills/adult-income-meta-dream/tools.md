# Tools

## Allowed
- read_traces - every fit row of the log so far (scope all)
- read_memory - the actor pack's cards
- read_pack - every file of the actor pack
- rank_policies - replay the log as a simulator for the named policies; zero fits
- patch_pack - one patch per visit to the actor's Search policy line; the human or the private gate decides

## Forbidden
- fit_recipe, score_test, save_model - the meta pack never trains and never touches the test split
- write_card - cards are the verifier's
- private_score, rollback - not needed here; the runner keeps versions/ as in lesson 09
