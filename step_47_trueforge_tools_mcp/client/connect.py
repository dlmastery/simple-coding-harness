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

from trueforge_sdk import TrueForge

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")


def connect(base_url: str = BASE_URL, timeout: float = 600) -> TrueForge:
    """Return a TrueForge client. No token: the local server runs in standalone mode."""
    return TrueForge(base_url=base_url, timeout=timeout)
