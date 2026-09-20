# Module: agent loop
1. Open the arm: `load_splits P T [--arm control --memory off]` and keep the profile.
2. Until a result says `FREEZE`: pick the next recipes as `modules/context.md` says and fit them in one call - `fit_recipe P T [--arm control] --recipes ...` - then read the result as `modules/observation.md` says.
3. When a result says `FREEZE`, do what `modules/completion.md` says.
