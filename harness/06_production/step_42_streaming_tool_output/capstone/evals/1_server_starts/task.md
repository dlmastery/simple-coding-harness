Check: the server starts. app.py imports, exposes a FastAPI instance named
`app`, its startup runs inside a TestClient, and `GET /health` answers 200
with `{"status": "ok"}`. No port is bound.
