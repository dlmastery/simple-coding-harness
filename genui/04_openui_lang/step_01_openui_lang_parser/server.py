"""Step 01 - a small static server with one SSE route.

GET /            the page (index.html) and its files
GET /stream      program.oui, one line per SSE message, with a delay between
                 lines (`?delay=400` in milliseconds) to make streaming visible
"""

from __future__ import annotations

import json
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).parent


def program_lines(path: Path = HERE / "program.oui") -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the demo output clean
        pass

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/stream":
            return super().do_GET()
        delay = int(parse_qs(url.query).get("delay", ["0"])[0]) / 1000
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for line in program_lines():
            self.wfile.write(f"data: {json.dumps(line)}\n\n".encode())
            self.wfile.flush()
            time.sleep(delay)
        self.wfile.write(b"event: done\ndata: {}\n\n")
        self.wfile.flush()


def make_server(port: int = 0) -> ThreadingHTTPServer:
    """Bind on `port` (0 picks a free one) and return the server, not yet serving."""
    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(HERE)))


if __name__ == "__main__":
    server = make_server(8004)
    print(f"http://127.0.0.1:{server.server_port}/")
    server.serve_forever()
