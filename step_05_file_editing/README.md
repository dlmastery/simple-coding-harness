# Stage 5 - File editing tools (video 25:08 - 26:32)

> "Let's continue building and add the biggest missing feature in our
> coding agent right now."

`tools.py` gains `write_file(path, content)` and
`str_replace(path, old_str, new_str)`, and the system prompt tells the
model to use them.

## The two tools

- **write_file** creates or overwrites a file. "It just invokes f.write."
- **str_replace** swaps one exact block of text for another. "The magic
  all happens inside the LLM because the LLM is the one that has to figure
  out from the context what file to edit, where to edit and what to
  replace it with." It refuses when `old_str` is not found or matches more
  than once; `allow_multi_edit` replaces every match - the video's
  "replace all" demo, where five `hello world` lines all become `goodbye`.

An error is returned as the tool's result string, not raised. The model
reads it and retries with a more specific `old_str`.

## Run it

```bash
python agent.py
> write a new file called hello.txt with five hello worlds
> replace every hello world with goodbye
```

"We now have a coding agent that can write files."

## Diff from stage 4

```bash
diff ../step_04_skills/tools.py tools.py
diff ../step_04_skills/llm.py llm.py
```
