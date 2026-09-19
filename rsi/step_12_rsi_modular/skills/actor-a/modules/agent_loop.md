# Module: agent loop
1. Call `load_splits` once and keep the profile.
2. For t in 1..24: pick ONE recipe as `modules/context.md` says, call `fit_recipe`, read the result as `modules/observation.md` says.
3. When a result says `FREEZE`, do what `modules/completion.md` says.
