Check: the CRUD endpoints work. Through a TestClient: the list starts empty;
POST /todos creates with 201 and the right shape, and rejects a missing title
with 422; GET /todos/{id} reads it back; PUT /todos/{id} changes only the
given fields; DELETE /todos/{id} returns 204; a missing id is 404 on GET,
PUT and DELETE.
