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

At this stage the app only starts. Task APIs will be added in the next phase.

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

At this stage `Task` is a plain Java object, not a database entity yet. Persistence will be added later so we can first focus on the domain language.

## Repository Layer

`TaskRepository` is the data access boundary for tasks.

For now it uses an in-memory `Map`, which means data disappears when the application stops.

This is intentional for the tutorial:

- It lets us learn the repository responsibility before adding a database.
- It keeps the first REST API simple.
- It creates a seam where we can later replace memory storage with H2/JPA.
