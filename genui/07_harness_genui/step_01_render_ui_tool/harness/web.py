"""Generative UI step 01 - the second surface: a browser page fed over SSE.

The terminal draws a spec with rich. With --web the same spec also goes to
every open browser tab as one SSE event. The server is the standard library
http.server in a daemon thread; the page is web/index.html + web/app.js.
"""

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8"}

subscribers = []      # one queue per open EventSource
latest = None         # the last spec, replayed to tabs that open later
lock = threading.Lock()


def publish(spec):
    """Hand a spec to every open tab and remember it for the next one."""
    global latest
    with lock:
        latest = spec
        for q in list(subscribers):
            q.put(spec)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # the terminal UI owns stdout

    def do_GET(self):
        if self.path == "/events":
            return self.events()
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

    def events(self):
        """Server-Sent Events: 'data: <spec json>' per render, the last spec first."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        q = queue.Queue()
        with lock:
            subscribers.append(q)
            if latest is not None:
                q.put(latest)
        try:
            while True:
                try:
                    spec = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")  # a comment line, so proxies do not close us
                else:
                    self.wfile.write(f"data: {json.dumps(spec)}\n\n".encode())
                self.wfile.flush()
        except (ConnectionError, OSError):
            pass
        finally:
            with lock:
                subscribers.remove(q)


def serve(port=8770):
    """Start the page server in the background and return the address."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
