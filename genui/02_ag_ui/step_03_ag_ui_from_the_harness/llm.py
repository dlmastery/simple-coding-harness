"""Settings for this step. The model calls themselves live in harness/llm.py,
the harness codelab's streaming call; this module only makes sure the
harness finds the same settings the other genui steps use.

API_KEY (OPENAI_API_KEY is accepted as an alias), BASE_URL and MODEL come
from the environment or from ~/.simple-harness/env, a KEY=VALUE file that
is read, never printed. Import this module before any harness module:
harness/config.py reads the environment when it is imported.
"""

import os
from pathlib import Path

try:  # on some machines Python needs the OS certificate store for live calls
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

ENV_FILE = Path.home() / ".simple-harness" / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
if "API_KEY" not in os.environ and "OPENAI_API_KEY" in os.environ:
    os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]
os.environ.setdefault("BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("MODEL", "gpt-4.1-mini")

BASE_URL = os.environ["BASE_URL"]
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ["MODEL"]
