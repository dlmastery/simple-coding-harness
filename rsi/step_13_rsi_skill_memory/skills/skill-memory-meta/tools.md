# Tools

## Allowed
- read_traces - this problem's fit rows (scope problem) and the profile
- read_memory - the actor's memory.json, if any (this pack keeps its memory as cards; the result may be empty)
- read_pack - every file of the actor pack, the cards included
- skill_memory - action update: one localised, validated card update

## Forbidden
- fit_recipe, score_test, save_model - the meta pack never trains and never touches the test split
- write_card, patch_pack - cards change through skill_memory only
