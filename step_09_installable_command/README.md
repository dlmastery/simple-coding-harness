# Stage 9 - An installable command

**What this stage adds:** packaging. The flat files move into a `harness/`
package, the loop moves inside `main()`, credentials get a config module,
and `pyproject.toml` declares a console script. The loop itself does not
change.

```text
harness/
├── agent.py      main(): the stage 8 loop, indented one level
├── config.py     new: BASE_URL / API_KEY / MODEL from the env or ~/.simple-harness/env
├── llm.py        reads config instead of os.environ
├── tools.py  skills.py  context.py  session.py  commands.py  ui.py   (relative imports)
pyproject.toml    [project.scripts] harness = "harness.agent:main"
```

## Files

```text
step_09_installable_command/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         main(): the stage 8 loop, indented one level
│   ├── commands.py      slash commands, unchanged from stage 8
│   ├── config.py        BASE_URL / API_KEY / MODEL from env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged from stage 8
│   ├── llm.py           call_llm reads its credentials from config.py
│   ├── session.py       transcripts on disk, unchanged from stage 8
│   ├── skills.py        skills, unchanged from stage 4
│   ├── tools.py         tools, unchanged from stage 8
│   └── ui.py            the presentation layer, unchanged from stage 8
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: the console script runs the loop; config
├── pyproject.toml       [project.scripts] harness = "harness.agent:main"; 0.9.0
└── README.md            this file
```

## The code, piece by piece

### 1. The entry point

`pyproject.toml`:

```text
[project.scripts]
harness = "harness.agent:main"
```

`harness/agent.py`:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    cli = parser.parse_args()

    ui.banner()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
```

```python
if __name__ == "__main__":
    main()
```

`pip install -e .` creates a `harness` executable that calls
`harness.agent.main`. `uv tool install .` does the same job. Because the
loop now runs from any directory, every "where am I" decision keys off the
current working directory: skills are looked up under that directory's
`.agents/skills`, sessions are filed under its name, and `git status` is
taken there.

### 2. Credentials in one place

`harness/config.py`:

```python
HOME = Path.home() / ".simple-harness"
ENV_FILE = HOME / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")
```

Real environment variables win; the file fills the gaps, so you set the
key once. `setdefault` is what makes the precedence work.

`harness/llm.py`:

```python
client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
MODEL = config.MODEL
```

### 3. Relative imports

Every `from tools import ...` became `from .tools import ...`. That is the
whole difference between a folder of scripts and a package.

## Run it

```bash
pip install -e .
cd ~/any/other/project
harness
```

or without installing: `python -m harness.agent` from this directory.

## Diff from stage 8

```bash
diff ../step_08_sessions_rewind/agent.py harness/agent.py   # four spaces and a def main()
cat harness/config.py
```
