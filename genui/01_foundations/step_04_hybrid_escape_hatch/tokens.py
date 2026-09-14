"""Step 03 - count what each generation mode made the model write.

The State of Generative UI report says open-ended HTML costs 5 to 10 times
the tokens of a declarative spec for the same screen. This module counts
with tiktoken's o200k_base (the GPT-4.1 family vocabulary) when it is
available, and the demo prints the API's own completion_tokens next to it.
"""

_encoding = None


def encoding():
    """The o200k_base encoder, loaded once, or None when tiktoken (or its vocabulary) is unavailable."""
    global _encoding
    if _encoding is None:
        try:
            import tiktoken

            _encoding = tiktoken.get_encoding("o200k_base")
        except Exception:  # not installed, or no network to fetch the vocabulary
            _encoding = False
    return _encoding or None


def count(text):
    """Tokens in the text, or None when no encoder is available."""
    enc = encoding()
    return len(enc.encode(text)) if enc else None


def table(rows):
    """rows: [(mode, what, raw_text, api_completion_tokens)] -> the printed comparison, as lines."""
    counted = [(mode, what, count(raw), api) for mode, what, raw, api in rows]
    base = next((n or api for mode, _, n, api in counted if mode == "flat"), None)
    lines = [f"{'mode':<7} {'what the model wrote':<28} {'tiktoken':>8} {'api':>6} {'vs flat':>8}"]
    for mode, what, n, api in counted:
        measured = n if n is not None else api
        ratio = f"{measured / base:.1f}x" if base and measured else "-"
        lines.append(f"{mode:<7} {what:<28} {n if n is not None else '-':>8} {api if api is not None else '-':>6} {ratio:>8}")
    return lines
