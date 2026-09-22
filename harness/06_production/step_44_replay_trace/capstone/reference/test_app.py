"""Tests for the todo API. Every test gets an empty database in a temp directory."""

import os

import pytest
from fastapi.testclient import TestClient

import app as todo_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_DB", str(tmp_path / "test.db"))
    with TestClient(todo_app.app) as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_is_empty_at_first(client):
    assert client.get("/todos").json() == []


def test_create_and_read(client):
    created = client.post("/todos", json={"title": "write tests"})
    assert created.status_code == 201
    todo = created.json()
    assert todo["title"] == "write tests" and todo["done"] is False and isinstance(todo["id"], int)
    assert client.get(f"/todos/{todo['id']}").json() == todo
    assert client.get("/todos").json() == [todo]


def test_update_changes_only_the_given_fields(client):
    todo = client.post("/todos", json={"title": "ship"}).json()
    updated = client.put(f"/todos/{todo['id']}", json={"done": True})
    assert updated.status_code == 200
    assert updated.json() == {"id": todo["id"], "title": "ship", "done": True}
    renamed = client.put(f"/todos/{todo['id']}", json={"title": "ship it"})
    assert renamed.json() == {"id": todo["id"], "title": "ship it", "done": True}


def test_delete_removes_the_todo(client):
    todo = client.post("/todos", json={"title": "gone"}).json()
    assert client.delete(f"/todos/{todo['id']}").status_code == 204
    assert client.get(f"/todos/{todo['id']}").status_code == 404
    assert client.get("/todos").json() == []


def test_missing_todo_is_404(client):
    assert client.get("/todos/999").status_code == 404
    assert client.put("/todos/999", json={"done": True}).status_code == 404
    assert client.delete("/todos/999").status_code == 404


def test_title_is_required(client):
    assert client.post("/todos", json={"done": True}).status_code == 422
