"""Stage 15 - settings. Real environment variables win; ~/.simple-harness/env fills gaps.

One KEY=VALUE per line, so the key is set once instead of exported in every
shell, the way a .env file would.
"""

import os
from pathlib import Path

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

# How much room the model has, and how we spend it (85% -> 35%).
CONTEXT_WINDOW = int(os.environ.get("CONTEXT_WINDOW", 128_000))
COMPACT_AT = 0.85  # compact once the prompt crosses this fraction of the window
COMPACT_TO = 0.35  # and cut back to this fraction, so it does not retrigger soon
