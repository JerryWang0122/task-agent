# backend-java

This folder will contain the Java Spring Boot REST API.

The backend is the business system. It will own:

- Task domain model
- Business rules
- REST endpoints
- Persistence

We build this before the Agent because an enterprise Agent usually calls existing business services instead of owning the database directly.
