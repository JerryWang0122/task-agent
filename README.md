# Personal Task Management Agent

This repository is a tutorial project for learning how an enterprise-style AI Agent system is usually separated into layers.

The final architecture will be:

```text
User
  -> Python Agent
  -> MCP Server
  -> Java Spring Boot Task API
  -> Database
```

## Project Structure

```text
backend-java/   Java Spring Boot REST API. Owns task data and business rules.
mcp-server/     MCP tool layer. Wraps backend APIs as Agent-callable tools.
agent-python/   Python Agent orchestration layer. Handles natural-language workflows.
docs/           Learning notes, diagrams, and phase-by-phase explanations.
```

## Current Learning Milestone

Phase 7 focuses on productizing the Agent workflow while preserving enterprise boundaries:

```text
Backend Java:
  owns task business rules and query semantics

MCP Server:
  exposes selected backend capabilities as Agent tools

Python Agent:
  owns orchestration, safety policy, follow-up questions, confirmation, and optional LangGraph routing
```

Examples now supported include:

```text
show overdue tasks
show high priority overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
```

The key lesson is that LangGraph organizes Agent workflow state and routing; it does not replace the backend, MCP tools, or Agent safety policy.

## Phase 0 Environment

This project targets Java 17 for the backend tutorial.

If Maven uses a newer JDK on your machine, run Maven with Java 17 explicitly:

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn -version
```

Expected Maven Java runtime:

```text
Java version: 17.x
```
