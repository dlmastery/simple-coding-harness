"""Settings. Real environment variables win; ~/.simple-harness/env fills gaps.

The env file is one KEY=VALUE per line, so you set your key once instead of
exporting it in every shell.
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

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")
