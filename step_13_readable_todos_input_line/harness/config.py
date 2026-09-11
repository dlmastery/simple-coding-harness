"""Stage 13 - settings. Real environment variables win; ~/.simple-harness/env fills gaps.

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
