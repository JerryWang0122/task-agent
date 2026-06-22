# Phase 6: Improve Agent Intelligence

## Goal

Phase 6 improves the Agent from simple tool execution toward useful task reasoning.

The first capability is overdue task lookup:

```text
User: Show me overdue tasks.
  -> Agent decides it needs overdue task data
  -> MCP tool find_overdue_tasks
  -> Java backend endpoint GET /api/tasks/overdue
  -> TaskService asks the repository for open tasks due before today
```

## Step 6.1: Overdue Task Query

### Concept

An overdue task is a business concept, not just a display trick.

In this project, overdue means:

```text
dueDate is before today
and status is not DONE
```

That rule belongs in the Java backend because the backend owns task business rules. The Agent should not directly inspect database tables or reinvent the rule differently from the rest of the system.

### Backend API

The Java backend now exposes:

```text
GET /api/tasks/overdue
```

The flow is:

```text
TaskController.findOverdueTasks()
  -> TaskService.findOverdueTasks(LocalDate.now())
  -> TaskJpaRepository.findByDueDateBeforeAndStatusNot(...)
  -> H2 database
```

### MCP Tool

The MCP Server now exposes:

```text
find_overdue_tasks
```

This tool calls:

```text
GET /api/tasks/overdue
```

The MCP Server stays thin. It does not calculate overdue dates itself.

### Agent Behavior

The Agent can now call the overdue tool through:

```text
overdue
show overdue tasks
ask-llm show overdue tasks
ask-tools show overdue tasks
```

`find_overdue_tasks` is read-only, so it does not require confirmation.

### Why This Design Matters

This step shows the difference between Agent intelligence and business rules:

```text
Agent intelligence:
  Understand that the user is asking about overdue work.

Backend business rule:
  Define exactly what overdue means.
```

That separation keeps the Agent flexible without making it the owner of core domain behavior.
