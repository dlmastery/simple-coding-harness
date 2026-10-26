"""One function, `chat`, for every model call in the course, with a replay cache.

Any OpenAI-compatible endpoint works (OpenAI, OpenRouter, a local Ollama):

    API_KEY=...                      # or OPENAI_API_KEY
    BASE_URL=https://api.openai.com/v1   # default; Ollama: http://localhost:11434/v1

Every response is stored in rsi/replay/ keyed by (model, messages,
temperature, sample). The course ships the cache from the author's runs, so

    RSI_LLM=replay   reproduces every number in the READMEs offline, free
    RSI_LLM=auto     uses the cache when it can and calls the model otherwise (default)
    RSI_LLM=live     always calls the model and records the new answer

`sample` lets one prompt have several independent answers: replica 0 and
replica 1 of the same attempt are different draws, both cached.
"""

import hashlib
import logging
import json
import os
import threading
import time
from pathlib import Path

CACHE_DIR = Path(os.environ.get("RSI_REPLAY_DIR", Path(__file__).resolve().parents[1] / "replay"))
_lock = threading.Lock()
logging.getLogger("httpx").setLevel(logging.WARNING)
_cache = None
_client = None
USAGE = {"calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0}


class ReplayMiss(RuntimeError):
    pass


def _key(model, messages, temperature, sample, effort):
    blob = json.dumps([model, messages, temperature, sample, effort], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _load():
    global _cache
    if _cache is None:
        _cache = {}
        if CACHE_DIR.exists():
            for shard in sorted(CACHE_DIR.glob("*.jsonl")):
                for line in shard.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        row = json.loads(line)
                        _cache[row["key"]] = row
    return _cache


def _store(row):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{row['key'][:2]}.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _live(model, messages, temperature, max_tokens, effort):
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(base_url=os.environ.get("BASE_URL", "https://api.openai.com/v1"),
                         api_key=os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY"),
                         timeout=180, max_retries=4)
    kwargs = {"model": model, "messages": messages, "temperature": temperature}
    if model.startswith(("gpt-5", "o")):
        kwargs["reasoning_effort"] = effort
        kwargs["max_completion_tokens"] = max_tokens * (1 if effort == "none" else 4)  # room for hidden reasoning
        if effort != "none":
            kwargs.pop("temperature")  # reasoning models only sample at their default temperature
    else:
        kwargs["max_tokens"] = max_tokens
    for attempt in range(5):
        try:
            r = _client.chat.completions.create(**kwargs)
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    u = r.usage
    return r.choices[0].message.content or "", (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


def chat(messages, model, temperature=0.7, sample=0, max_tokens=2000, effort="none"):
    """Return (text, prompt_tokens, completion_tokens). Cached by content and sample index.

    effort is the reasoning effort for reasoning models ("none", "low", "medium", "high").
    """
    mode = os.environ.get("RSI_LLM", "auto")
    key = _key(model, messages, temperature, sample, effort)
    with _lock:
        hit = _load().get(key) if mode != "live" else None
    if hit:
        with _lock:
            USAGE["cached"] += 1
            USAGE["prompt_tokens"] += hit["prompt_tokens"]
            USAGE["completion_tokens"] += hit["completion_tokens"]
        return hit["text"], hit["prompt_tokens"], hit["completion_tokens"]
    if mode == "replay":
        raise ReplayMiss(f"no cached answer for this {model} request; set RSI_LLM=auto and API_KEY to run it live")
    text, pt, ct = _live(model, messages, temperature, max_tokens, effort)
    row = {"key": key, "model": model, "sample": sample, "text": text, "prompt_tokens": pt, "completion_tokens": ct}
    with _lock:
        _cache[key] = row
        _store(row)
        USAGE["calls"] += 1
        USAGE["prompt_tokens"] += pt
        USAGE["completion_tokens"] += ct
    return text, pt, ct
