# Phase 1: Java Task API

## Goal

Build a normal Java Spring Boot REST API before adding MCP or a Python Agent.

Why:

- The Java backend owns the task business rules.
- The Agent should call backend capabilities instead of directly modifying data.
- A stable REST API makes the future MCP layer easier to test.

## Phase 1 Backend Layers

```text
TaskController
  -> TaskService
  -> TaskRepository
  -> in-memory Map
```

Phase 1 intentionally used an in-memory repository so we could learn the REST API layers before adding persistence.

Phase 2 has since evolved this path to:

```text
TaskController
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

Responsibilities:

- `TaskController`: HTTP boundary
- `TaskService`: business workflows
- `TaskRepository`: Phase 1 in-memory data access boundary
- `Task`: domain model
- DTO classes: API request and response shapes

## Current REST Endpoints

```text
GET    /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks
PATCH  /api/tasks/{id}/complete
DELETE /api/tasks/{id}
```

## Start the Backend

From the repository root:

```bash
cd backend-java
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn spring-boot:run
```

The backend runs on:

```text
http://localhost:8080
```

## Manual API Test with curl

List tasks:

```bash
curl http://localhost:8080/api/tasks
```

Expected result after a fresh app start:

```json
[]
```

Create a task:

```bash
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Prepare weekly report","description":"Draft the weekly status update","priority":"HIGH","dueDate":"2026-06-17"}'
```

Expected result:

```json
{
  "id": 1,
  "title": "Prepare weekly report",
  "description": "Draft the weekly status update",
  "status": "TODO",
  "priority": "HIGH",
  "dueDate": "2026-06-17"
}
```

Get one task:

```bash
curl http://localhost:8080/api/tasks/1
```

Complete a task:

```bash
curl -X PATCH http://localhost:8080/api/tasks/1/complete
```

Expected status field:

```json
"status": "DONE"
```

Delete a task:

```bash
curl -i -X DELETE http://localhost:8080/api/tasks/1
```

Expected HTTP status:

```text
204 No Content
```

Verify the task is gone:

```bash
curl -i http://localhost:8080/api/tasks/1
```

Expected HTTP status:

```text
404 Not Found
```

## What This Proves

This verifies that the backend can be used by an external client over HTTP.

That matters because the future MCP Server will also behave like a client of this backend API.

## Phase 1 Limitation

Tasks are stored in memory, so data disappears when the backend restarts.

This was intentional for Phase 1. Phase 2 replaces the in-memory repository with Spring Data JPA and H2.
