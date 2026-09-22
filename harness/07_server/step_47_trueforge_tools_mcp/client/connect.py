"""Step 47 - one place that builds the TrueForge client.

`truststore` makes Python's HTTPS clients trust the Windows certificate
store. It is injected before any HTTP client exists, and skipped when the
package is missing. Every module in this step gets its client from here.
"""

import os

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

import httpx
from trueforge_sdk import TrueForge
from trueforge_sdk.core.api_error import ApiError

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")
REQUEST_ERRORS = (httpx.HTTPError, ApiError)  # the server is unreachable, or it answered with an error status


def describe_error(error, base_url: str = BASE_URL) -> str:
    """One line for a failed request: the server and what came back."""
    if isinstance(error, ApiError):
        return f"{base_url} answered {error.status_code}: {str(error.body)[:200]}"
    return f"{base_url} is not answering ({type(error).__name__}: {error})"


def connect(base_url: str = BASE_URL, timeout: float = 600) -> TrueForge:
    """Return a TrueForge client. No token: the local server runs in standalone mode."""
    return TrueForge(base_url=base_url, timeout=timeout)
