"""Step 38 - check 2: create, read, update and delete through the API, and the 404s."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import client, fail, load_app, ok  # noqa: E402

try:
    app = load_app()
except Exception as error:  # noqa: BLE001
    fail(f"app.py did not import: {type(error).__name__}: {error}")


def expect(condition, message):
    if not condition:
        fail(message)


with client(app) as http:
    expect(http.get("/todos").json() == [], "GET /todos on an empty database must return []")

    created = http.post("/todos", json={"title": "write the checks"})
    expect(created.status_code == 201, f"POST /todos returned {created.status_code}, expected 201")
    todo = created.json()
    expect(isinstance(todo.get("id"), int), f"POST /todos returned no integer id: {todo}")
    expect(todo.get("title") == "write the checks" and todo.get("done") is False, f"POST /todos returned the wrong body: {todo}")
    expect(set(todo) == {"id", "title", "done"}, f"a todo must have exactly id, title and done: {todo}")
    first_id = todo["id"]

    expect(http.post("/todos", json={"done": True}).status_code == 422, "POST /todos without a title must be 422")

    second = http.post("/todos", json={"title": "second", "done": True}).json()
    listed = http.get("/todos").json()
    expect([t["id"] for t in listed] == [first_id, second["id"]], f"GET /todos must list oldest first: {listed}")

    read = http.get(f"/todos/{first_id}")
    expect(read.status_code == 200 and read.json() == todo, f"GET /todos/id returned {read.status_code} {read.text}")

    updated = http.put(f"/todos/{first_id}", json={"done": True})
    expect(updated.status_code == 200, f"PUT /todos/id returned {updated.status_code}")
    expect(updated.json() == {"id": first_id, "title": "write the checks", "done": True}, f"PUT must change only the given fields: {updated.json()}")
    renamed = http.put(f"/todos/{first_id}", json={"title": "renamed"})
    expect(renamed.json() == {"id": first_id, "title": "renamed", "done": True}, f"PUT must keep done when only title is given: {renamed.json()}")

    deleted = http.delete(f"/todos/{first_id}")
    expect(deleted.status_code == 204, f"DELETE /todos/id returned {deleted.status_code}, expected 204")
    expect(deleted.content == b"", "DELETE must return an empty body")
    expect(http.get(f"/todos/{first_id}").status_code == 404, "a deleted todo must be 404")
    expect(http.get("/todos").json() == [second], "the list must shrink after a delete")

    expect(http.get("/todos/424242").status_code == 404, "GET of a missing id must be 404")
    expect(http.put("/todos/424242", json={"done": True}).status_code == 404, "PUT of a missing id must be 404")
    expect(http.delete("/todos/424242").status_code == 404, "DELETE of a missing id must be 404")

ok("create, read, update, delete and the 404s all behave")
