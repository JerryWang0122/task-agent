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
