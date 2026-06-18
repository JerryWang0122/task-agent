# Phase 2: Persistence and Seed Data

## Goal

Add persistence to the Java backend so task data flows through a database-backed repository instead of an in-memory collection.

Why:

- The future MCP Server needs stable backend capabilities to call.
- The Python Agent should work with realistic task data.
- Persistence makes the backend closer to an enterprise business service.

## Current Backend Layers

```text
TaskController
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

Responsibilities:

- `TaskController`: HTTP boundary
- `TaskService`: business workflows and default task rules
- `TaskJpaRepository`: Spring Data JPA data access boundary
- `Task`: JPA entity and domain model
- `TaskDataSeeder`: startup sample data
- DTO classes: API request and response shapes

## Persistence Components

### Maven Dependencies

`spring-boot-starter-data-jpa` provides:

- JPA repository support
- Hibernate ORM
- transaction infrastructure
- entity mapping support

`h2` provides:

- an embedded local database
- a browser database console
- a lightweight development database for this tutorial

### JPA Entity

`Task` is mapped to the `tasks` table.

Important mapping choices:

- `@Entity`: marks the class as database-mapped
- `@Table(name = "tasks")`: names the database table
- `@Id`: marks the primary key
- `@GeneratedValue(strategy = GenerationType.IDENTITY)`: lets the database generate ids
- `@Enumerated(EnumType.STRING)`: stores enum values as readable strings

### Repository

`TaskJpaRepository` extends:

```java
JpaRepository<Task, Long>
```

Spring Data JPA automatically provides common operations such as:

- `findAll()`
- `findById()`
- `save()`
- `deleteById()`
- `existsById()`
- `count()`

## H2 Configuration

The backend uses:

```properties
spring.datasource.url=jdbc:h2:mem:taskdb
spring.h2.console.enabled=true
spring.h2.console.path=/h2-console
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.open-in-view=false
```

H2 console:

```text
http://localhost:8080/h2-console
```

Connection settings:

```text
JDBC URL: jdbc:h2:mem:taskdb
User Name: sa
Password: empty
```

## Seed Data

`TaskDataSeeder` runs when Spring Boot starts.

It checks:

```java
taskRepository.count()
```

If the table is empty, it creates 4 sample tasks:

- A task due today
- A future task
- An overdue task
- A completed task

This gives future MCP tools and the Python Agent useful data for queries like:

- "What tasks are due today?"
- "Show overdue tasks."
- "Find urgent tasks."
- "Show completed tasks."

## Manual Verification with curl

Start the backend:

```bash
cd backend-java
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn spring-boot:run
```

List tasks:

```bash
curl http://localhost:8080/api/tasks
```

Expected result:

```text
The response contains 4 seeded tasks after a fresh startup.
```

Create one more task:

```bash
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Manual persistence check","description":"Created during manual verification","priority":"MEDIUM","dueDate":"2026-06-21"}'
```

Expected result:

```text
The response contains a new task with the next generated id.
```

Get the new task:

```bash
curl http://localhost:8080/api/tasks/5
```

Expected result after a fresh seeded startup:

```text
The response returns the manually created task.
```

## What This Proves

This verifies that the backend now has a working persistence path:

```text
HTTP request
  -> TaskController
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

It also proves that startup seed data is available through the same REST API that future MCP tools will call.

## Current Limitation

The H2 database is still in-memory:

```text
jdbc:h2:mem:taskdb
```

Data disappears when the backend process stops.

This is acceptable for the tutorial because sample data is recreated on startup. A later production-style version could switch to file-based H2, PostgreSQL, or another durable database.
