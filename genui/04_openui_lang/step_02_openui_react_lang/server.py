"""Step 02 - the server: static files plus one streaming route.

GET  /            index.html, style.css, static/bundle.js
POST /generate    {"prompt": "..."} -> SSE stream of the model's text deltas,
                  each as `data: <json string>`, then `event: done`

The system prompt is prompt.txt, generated from library.mjs by prompt.mjs.
The server never parses the OpenUI Lang; the page does that with
@openuidev/react-lang as the text arrives.
"""

from __future__ import annotations

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import llm
from nodetools import ensure_prompt

HERE = Path(__file__).parent
LAST = {"program": ""}  # the most recent complete program, for the demo


def messages_for(prompt: str, system_prompt: str) -> list[dict]:
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]


class Handler(SimpleHTTPRequestHandler):
    # HTTP/1.1 keeps the connection open between the page's requests. With
    # HTTP/1.0 Chromium resets the connection halfway through the 1.5 MB bundle.
    protocol_version = "HTTP/1.1"
    system_prompt = ""

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")  # the stream ends when the socket closes
        self.end_headers()
        program = []
        for delta in llm.stream_completion(messages_for(body.get("prompt", ""), self.system_prompt)):
            program.append(delta)
            self.wfile.write(f"data: {json.dumps(delta)}\n\n".encode())
            self.wfile.flush()
        LAST["program"] = "".join(program)
        self.wfile.write(b"event: done\ndata: {}\n\n")
        self.wfile.flush()


def make_server(port: int = 0, system_prompt: str | None = None) -> ThreadingHTTPServer:
    """Bind on `port` (0 picks a free one); the caller starts serve_forever()."""
    Handler.system_prompt = ensure_prompt() if system_prompt is None else system_prompt
    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(HERE)))


if __name__ == "__main__":
    from nodetools import ensure_bundle

    ensure_bundle()
    server = make_server(8004)
    print(f"http://127.0.0.1:{server.server_port}/")
    server.serve_forever()
