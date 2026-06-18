# backend-java

This folder will contain the Java Spring Boot REST API.

The backend is the business system. It will own:

- Task domain model
- Business rules
- REST endpoints
- Persistence

We build this before the Agent because an enterprise Agent usually calls existing business services instead of owning the database directly.

## Run the Backend

Use Java 17 for this tutorial:

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn spring-boot:run
```

From the repository root, run:

```bash
cd backend-java
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn test
```

The app exposes task REST APIs and stores tasks through JPA/H2.

## Task Domain Model

The first business concept in this backend is `Task`.

Initial fields:

- `id`: unique task identifier
- `title`: short task name
- `description`: optional task details
- `status`: current task state, represented by `TaskStatus`
- `priority`: task importance, represented by `TaskPriority`
- `dueDate`: optional deadline
- `createdAt`: when the task was created
- `updatedAt`: when the task was last changed

`Task` is now also a JPA entity, so Hibernate can map it to the `tasks` database table.

## Repository Layer

`TaskJpaRepository` is the data access boundary for tasks.

It extends Spring Data JPA's `JpaRepository`, so Spring generates common CRUD operations for us.

Current repository responsibilities:

- Save tasks
- Find tasks by id
- List tasks
- Delete tasks
- Delegate SQL generation to Spring Data JPA and Hibernate

## Service Layer

`TaskService` contains task business workflows.

Current responsibilities:

- List tasks
- Get one task by id
- Create a task with default status and priority
- Mark a task as completed
- Delete a task

The service depends on `TaskJpaRepository`, but controllers and future MCP tools should depend on the service instead of directly modifying storage.

## REST API Layer

`TaskController` exposes task capabilities over HTTP.

Current endpoints:

```text
GET    /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks
PATCH  /api/tasks/{id}/complete
DELETE /api/tasks/{id}
```

DTOs define the API contract:

- `CreateTaskRequest`: JSON shape accepted when creating a task
- `TaskResponse`: JSON shape returned to API clients

The controller maps HTTP requests to service calls. It should not contain core business rules.
