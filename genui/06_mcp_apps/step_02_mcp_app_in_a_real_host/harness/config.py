"""Stage 15 - settings. Real environment variables win; ~/.simple-harness/env fills gaps.

One KEY=VALUE per line, so the key is set once instead of exported in every
shell, the way a .env file would. This copy follows the generative UI
series: OPENAI_API_KEY fills API_KEY, and the defaults are OpenAI's.
"""

import os
from pathlib import Path

try:
    import truststore

    truststore.inject_into_ssl()  # this machine's TLS proxy needs the system store
except ImportError:
    pass

HOME = Path.home() / ".simple-harness"
ENV_FILE = HOME / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")

# How much room the model has, and how we spend it (85% -> 35%).
CONTEXT_WINDOW = int(os.environ.get("CONTEXT_WINDOW", 128_000))
COMPACT_AT = 0.85  # compact once the prompt crosses this fraction of the window
COMPACT_TO = 0.35  # and cut back to this fraction, so it does not retrigger soon
