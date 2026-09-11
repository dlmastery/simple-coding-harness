# Stage 2.3 - A read_file tool (video 10:57 - 12:07)

> "Let's add that next tool into this agent's capabilities and that is going
> to be the read file tool."

`tools.py` gains `read_file(path)` and its schema. `llm.py` does not change
except for the docstring - that is the point of stage 2.2.

Run it and ask *can you read the llm.py file*: the model calls `read_file`
and the whole file is printed.

## The problem this stage makes visible

"We are able to generate tool call arguments from the LLM. And we are also
able to execute them. However, we are not passing those results back to the
language model for it to actually do anything." The model reads the file
into *our* terminal, not into its own context. Stage 2.4 fixes that, and
that is where the video first uses the word *agent*.

## Diff from stage 2.2

```bash
diff ../step_02_2_generic_tools/tools.py tools.py
```
