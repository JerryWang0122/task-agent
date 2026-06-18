# Phase 3: MCP Server

## Goal

Expose selected Java backend capabilities as MCP tools that an Agent can call.

The MCP Server should stay thin:

```text
MCP tool
  -> calls Java REST API
  -> returns structured data to the Agent
```

It should not:

- connect to the database directly
- duplicate Java business logic
- bypass `TaskService`
- know JPA or H2 details

## Language Choice Note

The company context for this learning project is Java-heavy.

For the tutorial, we are starting the MCP Server in Python because:

- the future Agent layer will also be Python
- Python `FastMCP` makes the MCP concept easy to learn
- the MCP layer stays clearly separate from the Java business backend
- we can focus on tool design before framework integration details

This does not mean MCP Servers should always be Python.

In a Java-heavy enterprise environment, a Java MCP Server can be a strong production choice because it can reuse:

- Spring Boot deployment patterns
- Java observability and logging standards
- existing authentication and authorization libraries
- existing CI/CD pipelines
- team Java knowledge

Planned follow-up after the first Python MCP path works:

```text
Compare Python MCP Server vs Java MCP Server for enterprise usage.
```

The key architectural rule remains the same in either language:

```text
MCP Server calls the Java REST API.
The Java backend owns task business logic and persistence.
```
