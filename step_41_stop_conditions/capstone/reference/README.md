# Todo API

A small todo list API built with FastAPI and stored in a SQLite file.

## Run

Install the dependencies, then start the server:

```
pip install fastapi uvicorn httpx pytest
uvicorn app:app --reload
```

The API listens on http://127.0.0.1:8000. The interactive docs are at
http://127.0.0.1:8000/docs. The database is `todos.db` in the working
directory; set `TODO_DB` to use another file.

## Endpoints

| Method | Path | Body | Result |
|--------|------|------|--------|
| GET | `/health` | - | `{"status": "ok"}` |
| GET | `/todos` | - | list of todos |
| POST | `/todos` | `{"title": str, "done": bool}` | 201, the new todo |
| GET | `/todos/{id}` | - | the todo, or 404 |
| PUT | `/todos/{id}` | `{"title"?: str, "done"?: bool}` | the updated todo, or 404 |
| DELETE | `/todos/{id}` | - | 204, or 404 |

A todo is `{"id": int, "title": str, "done": bool}`.

## Test

```
python -m pytest -q
```
