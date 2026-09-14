"""Step 46 - Register the OpenAI model provider on a TrueForge server.

Reads OPENAI_API_KEY from ~/.simple-harness/env (or the environment), PUTs one
provider manifest with one model, and prints the model list. Safe to run
again: the same manifest replaces itself. The key is never printed.

    python setup_server.py
"""

import os
import sys
from pathlib import Path

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from trueforge_sdk import ConfiguredModel, ModelProperties, ModelProviderAuth, OpenAiModelProvider, TrueForge

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")
ENV_FILE = Path.home() / ".simple-harness" / "env"

# One model, named the way TrueForge addresses it: `openai/gpt-4-1-mini`.
MODEL_ID = "gpt-4.1-mini"
MODEL_NAME = "gpt-4-1-mini"
CONTEXT_LENGTH = 1_047_576
MAX_OUTPUT_TOKENS = 32_768


def read_key(env_file=None):
    """OPENAI_API_KEY from the environment, else from the KEY=value lines of the env file."""
    env_file = ENV_FILE if env_file is None else env_file  # resolved at call time, so tests can point elsewhere
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENAI_API_KEY" and value.strip():
                return value.strip()
    return None


def manifest(api_key):
    """The provider manifest the server stores. Well-known types are named by their type."""
    return OpenAiModelProvider(
        auth=ModelProviderAuth(api_key=api_key),
        models=[
            ConfiguredModel(
                model_id=MODEL_ID,
                name=MODEL_NAME,
                properties=ModelProperties(context_length=CONTEXT_LENGTH, max_output_tokens=MAX_OUTPUT_TOKENS),
            )
        ],
    )


def main():
    key = read_key()
    if not key:
        print(f"no OPENAI_API_KEY in the environment or in {ENV_FILE}", file=sys.stderr)
        return 1
    client = TrueForge(base_url=BASE_URL, timeout=60)
    client.settings.model_providers.create_or_update(manifest=manifest(key))
    for provider in client.settings.model_providers.list().data:
        for model in provider.manifest.models:
            print(f"{provider.name}/{model.name}  ->  {model.model_id}  (context {model.properties.context_length:,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
