Build a small todo API in this directory. It is empty. Work only inside it.

Requirements:

1. `app.py` defines a FastAPI application in a module-level variable named
   `app`. Todos live in a SQLite database through the standard library
   `sqlite3` module. The database file path comes from the environment
   variable `TODO_DB` and defaults to `todos.db`. Read the variable when a
   connection is opened, not when the module is imported. Create the table
   on startup if it is missing.
2. A todo is `{"id": int, "title": str, "done": bool}`. Endpoints:
   - `GET /health` returns `{"status": "ok"}`.
   - `GET /todos` returns the list of todos, oldest first.
   - `POST /todos` takes `{"title": str, "done": bool}` (`done` defaults to
     false), returns the new todo with status 201. A body without a title
     is rejected with 422.
   - `GET /todos/{id}` returns the todo, or 404 when there is none.
   - `PUT /todos/{id}` takes `{"title": str, "done": bool}` where both
     fields are optional, changes only the fields given, returns the
     updated todo, or 404.
   - `DELETE /todos/{id}` returns 204 with an empty body, or 404.
3. `test_app.py` holds pytest tests that cover every endpoint through
   `fastapi.testclient.TestClient`. Each test must use its own temporary
   database file: set `TODO_DB` before the client opens. Run
   `python -m pytest -q` and make it pass before you finish.
4. `README.md` describes the project, has a `## Run` section with the
   `uvicorn app:app` command, and lists the endpoints.

fastapi, httpx and pytest are installed. Do not install packages, do not
start a server, and do not create files outside this directory. When the
tests pass, answer with a short summary of what you built.
