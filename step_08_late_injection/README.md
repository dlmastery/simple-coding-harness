# Step 8 - Late injection

**New in this step:** an `<env>` block (time, git branch) attached to every
request, at the end, and never stored.

```
request = messages + [ {"role": "user", "content": "<env>...</env>"} ]
                       └── built fresh each call, thrown away after ──┘
```

## The problem it solves

Some facts change while the session runs: the clock, the branch, and in the
next steps which files changed and what the plan is. Where do they go?

- In the **system prompt**? It is written once at startup and would go
  stale.
- Appended to **`messages`** every call? The transcript fills with dozens
  of copies of the same block.
- Rewritten **in place** near the top? Then the prefix of the prompt
  changes every call, and that has a cost most people do not see.

## Prompt caching, in one paragraph

Every call re-sends the whole conversation. Providers cache the longest
prefix that matches a previous request, and charge a fraction for those
tokens. The cache only helps if the prefix is *byte-identical*. Change one
character in message 3 and messages 3 through 300 are re-processed at full
price. So the rule for a harness is: **stable things at the front, volatile
things at the back, and never edit the middle.** Late injection is the
back-of-the-list half of that rule. Step 13 is the never-edit-the-middle
half.

Watch the `cached` number in the usage line. On a provider that supports
caching it should be most of the prompt from the second call onward.

## The UI shows the block

The dim "late injection" panel is there so you can see exactly what the
model sees. Everything a harness injects should be visible to the person
driving it; hidden context is how agents get confusing.

## Run it

```bash
python -m harness
you> what branch am I on and what time is it?
```

No tool call needed - it reads the answer off the block.

## Diff from step 7

```bash
diff -r ../step_07_editing_tools/harness harness
```

New: `context.py`. Changed: `agent.py` (three lines in `turn()`), `ui.py`
(the panel).
