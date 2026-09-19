"""Generative UI step 02 - serve the page and stream one OpenUI program to it.

Same shape as step 01's web surface: the standard library http.server in a
daemon thread and an SSE endpoint. The event is different. Step 01 pushed a
whole json-render spec per render; here every event is one line of OpenUI
Lang, so the page shows the skeleton fill in the way the TrueForge chat UI
does while the model is still writing. A null line means the program ended.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent / "web"
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8"}

program = ""    # the OpenUI Lang program to stream
reply = ""      # the raw reply it came from, for /reply
delay = 0.08    # seconds between lines, so the streaming is visible


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/events":
            return self.events()
        if self.path == "/reply":
            return self.text(reply)
        name = "index.html" if self.path in ("/", "") else self.path.lstrip("/")
        file = (WEB_DIR / name).resolve()
        if WEB_DIR.resolve() not in file.parents or not file.is_file() or file.suffix not in CONTENT_TYPES:
            self.send_error(404)  # only the page's own files: `..` in the path stays inside web/
            return
        body = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES[file.suffix])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def text(self, body):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def events(self):
        """One SSE event per program line, then `null` to say the program is complete."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for line in program.splitlines():
                self.wfile.write(f"data: {json.dumps(line)}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(delay)
            self.wfile.write(b"data: null\n\n")
            self.wfile.flush()
        except (ConnectionError, OSError):
            pass


def serve(openui_program, raw_reply="", port=8771, line_delay=0.08):
    """Start the server in the background and return (server, url)."""
    global program, reply, delay
    program, reply, delay = openui_program, raw_reply, line_delay
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
