# Stage 9 - An installable command (video 30:30)

> "I have also installed agent.py as a UV tool. And now it's called
> neuralcode."

The flat files move into a package, the loop moves inside `main()`, and
`pyproject.toml` declares a console script. Nothing in the loop changes.

```
harness/
├── agent.py      main(): the stage 8 loop, indented one level
├── config.py     new: BASE_URL / API_KEY / MODEL from env or ~/.simple-harness/env
├── llm.py        reads config instead of os.environ
├── tools.py  skills.py  context.py  session.py  commands.py  ui.py   (relative imports)
pyproject.toml    [project.scripts] harness = "harness.agent:main"
```

```bash
pip install -e .          # the video uses `uv tool install`
cd ~/any/other/project
harness
```

The project is wherever you run it: skills are found under that
directory's `.agents/skills`, sessions are filed under its name, and git
status is taken there. The video's command is `neuralcode`; this one is
`harness`.

## Diff from stage 8

Every `from x import` became `from .x import`, and `agent.py` gained four
spaces of indentation and a `def main():`. Compare the loop itself:

```bash
diff ../step_08_sessions_rewind/agent.py harness/agent.py
```
