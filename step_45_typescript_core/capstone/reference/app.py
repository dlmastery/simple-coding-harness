"""A small todo API: FastAPI on top of a SQLite file.

The database path comes from the TODO_DB environment variable and defaults
to todos.db in the working directory. Every request opens its own
connection, so the file can be swapped between tests.
"""

import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel


def db_path() -> str:
    """Where the SQLite file lives. Read per call, so tests can point it elsewhere."""
    return os.environ.get("TODO_DB", "todos.db")


@contextmanager
def connect():
    """One connection per request, committed on success and always closed."""
    connection = sqlite3.connect(db_path())
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    """Create the todos table when it is missing."""
    with connect() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS todos ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL, "
            "done INTEGER NOT NULL DEFAULT 0)"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: make sure the table exists before the first request."""
    init_db()
    yield


app = FastAPI(title="Todo API", lifespan=lifespan)


class TodoIn(BaseModel):
    """The body of a create request."""

    title: str
    done: bool = False


class TodoUpdate(BaseModel):
    """The body of an update request. Every field is optional."""

    title: str | None = None
    done: bool | None = None


class Todo(BaseModel):
    """One stored todo."""

    id: int
    title: str
    done: bool


def to_todo(row: sqlite3.Row) -> Todo:
    return Todo(id=row["id"], title=row["title"], done=bool(row["done"]))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    with connect() as connection:
        rows = connection.execute("SELECT id, title, done FROM todos ORDER BY id").fetchall()
    return [to_todo(row) for row in rows]


@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo: TodoIn) -> Todo:
    with connect() as connection:
        cursor = connection.execute("INSERT INTO todos (title, done) VALUES (?, ?)", (todo.title, int(todo.done)))
        row = connection.execute("SELECT id, title, done FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return to_todo(row)


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    with connect() as connection:
        row = connection.execute("SELECT id, title, done FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return to_todo(row)


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, update: TodoUpdate) -> Todo:
    with connect() as connection:
        row = connection.execute("SELECT id, title, done FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="todo not found")
        title = row["title"] if update.title is None else update.title
        done = row["done"] if update.done is None else int(update.done)
        connection.execute("UPDATE todos SET title = ?, done = ? WHERE id = ?", (title, done, todo_id))
        row = connection.execute("SELECT id, title, done FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return to_todo(row)


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> Response:
    with connect() as connection:
        deleted = connection.execute("DELETE FROM todos WHERE id = ?", (todo_id,)).rowcount
    if not deleted:
        raise HTTPException(status_code=404, detail="todo not found")
    return Response(status_code=204)
