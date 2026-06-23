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

## Step 6.2: Priority-Aware Overdue Queries

### Goal

The Agent can now answer more specific overdue questions:

```text
Show high priority overdue tasks.
Show overdue tasks grouped by priority.
```

### Concept

This step separates filtering from presentation:

```text
Filtering by priority:
  Backend business query

Grouping by priority:
  Agent response formatting
```

Filtering belongs in the backend because it changes which task records are selected. Grouping belongs in the Agent for now because it only changes how the already-selected records are shown to the user.

### Backend API

The existing endpoint now supports an optional query parameter:

```text
GET /api/tasks/overdue
GET /api/tasks/overdue?priority=HIGH
GET /api/tasks/overdue?priority=URGENT
```

The backend flow is:

```text
TaskController.findOverdueTasks(priority)
  -> if priority is missing: TaskService.findOverdueTasks(today)
  -> if priority is present: TaskService.findOverdueTasksByPriority(today, priority)
  -> TaskJpaRepository
```

### MCP Tool

The MCP tool remains the same tool name:

```text
find_overdue_tasks
```

But it now accepts an optional parameter:

```json
{
  "priority": "HIGH"
}
```

Keeping the same tool name is intentional. The user is still asking for overdue tasks; priority is just a filter.

### Agent Behavior

The Agent can now handle:

```text
overdue
show overdue tasks
show high priority overdue tasks
show overdue tasks grouped by priority
```

For grouped output, the Agent calls `find_overdue_tasks` without a priority filter and groups the returned records in the final response.

### What This Teaches

This is an early example of Agent orchestration:

```text
The Agent does not own the overdue rule.
The Agent can still decide how to present overdue results.
```

That is the balance we want in enterprise Agent design: business rules stay in backend services, while the Agent handles user intent and response composition.

## Step 6.3: Weekly Workload Summary

### Goal

The Agent can now answer questions about tasks due this week:

```text
weekly
What tasks are due this week?
Summarize my weekly workload.
```

### Concept

This step separates date-range querying from workload summarization:

```text
Date-range query:
  Backend capability

This week calculation:
  Agent interpretation for now

Summary formatting:
  Agent response composition
```

The backend should know how to query tasks by an explicit date range. The Agent can translate a user phrase like `this week` into concrete dates and then summarize the returned records.

### Backend API

The Java backend now exposes:

```text
GET /api/tasks/due-between?startDate=2026-06-22&endDate=2026-06-28
```

The range is inclusive:

```text
startDate <= dueDate <= endDate
```

The query returns open tasks only, so tasks with `DONE` status are excluded from the workload summary.

The backend flow is:

```text
TaskController.findTasksDueBetween(startDate, endDate)
  -> TaskService.findTasksDueBetween(startDate, endDate)
  -> TaskJpaRepository.findByDueDateBetweenAndStatusNot(...)
  -> H2 database
```

### MCP Tool

The MCP Server now exposes:

```text
find_tasks_due_between
```

Input shape:

```json
{
  "start_date": "2026-06-22",
  "end_date": "2026-06-28"
}
```

The MCP Server converts those Python-style parameter names into the Java REST query parameters:

```text
startDate
endDate
```

### Agent Behavior

The Agent supports:

```text
weekly
this week
what tasks are due this week
summarize my weekly workload
```

For now, `this week` means Monday through Sunday of the current local week.

The Agent runtime normalizes `this week` deterministically. This is important because the LLM may not know the current date, or may guess a stale date. If OpenAI chooses `find_tasks_due_between` for a message like `what tasks are due this week`, the Agent overwrites the tool arguments with the runtime-calculated current week before execution.

The Agent response includes:

```text
total open tasks due this week
counts by priority
counts by status
task list
```

### What This Teaches

This is a small example of Agent orchestration:

```text
The backend provides a reusable date-range task query.
The MCP Server exposes that query as an Agent tool.
The Agent turns user language into dates and summarizes the result.
```

In a later step, vague date handling can become more robust instead of hardcoding only `this week`.

## Step 6.4: Vague Date Handling

### Goal

The Agent can now handle more relative date phrases:

```text
tasks due today
tasks due tomorrow
tasks due next week
tasks due by Friday
```

### Concept

LLMs are not reliable clocks.

The model may understand that the user is asking about `this week`, but it may guess the wrong actual dates. For production Agent design, deterministic facts should come from the runtime, not from the model.

The rule is:

```text
LLM interprets intent.
Agent runtime calculates dates.
MCP executes tools.
Backend queries data.
```

### Runtime Date Normalization

The Agent now has a deterministic date parser for supported phrases:

```text
today      -> today to today
tomorrow   -> tomorrow to tomorrow
this week  -> current Monday to current Sunday
weekly     -> current Monday to current Sunday
next week  -> next Monday to next Sunday
by Friday  -> today to upcoming Friday
```

All of these become calls to the same reusable MCP tool:

```text
find_tasks_due_between
```

Example:

```text
User: tasks due by Friday
  -> Agent calculates start_date=today and end_date=upcoming Friday
  -> MCP find_tasks_due_between(start_date, end_date)
  -> Java GET /api/tasks/due-between?startDate=...&endDate=...
```

### LLM Safety Fix

If OpenAI returns stale dates for a relative-date request, the Agent overwrites them before execution.

Example bad model output:

```json
{
  "tool_name": "find_tasks_due_between",
  "arguments": {
    "start_date": "2024-04-21",
    "end_date": "2024-04-27"
  }
}
```

The Agent runtime replaces those arguments with the current calculated range before calling MCP.

### What This Teaches

This is a core Agent engineering pattern:

```text
Do not trust the LLM for deterministic facts.
Normalize and validate tool arguments in runtime policy.
```

Dates are just one example. The same principle later applies to user identity, permissions, account IDs, environment, and destructive action policy.

## Step 6.5: Follow-Up Questions

### Goal

The Agent should not guess missing information for write operations.

Example:

```text
User: create a task for tomorrow
```

This request has a due date, but it does not have a task title. The Agent should ask a follow-up question instead of inventing a title.

### Concept

Follow-up questions are part of safe Agent workflow design.

The rule is:

```text
If required information is missing, ask.
If the action changes data, confirm before execution.
```

This creates a two-stage flow:

```text
User request
  -> Agent detects missing title
  -> Agent asks follow-up question
  -> User provides title
  -> Agent asks confirmation
  -> User confirms
  -> MCP create_task
  -> Java backend
```

### Agent Behavior

The local create-task flow now supports:

```text
create a task for tomorrow
What is the task title? I will set the due date to 2026-06-23.
Buy milk
Confirm: create task 'Buy milk' due 2026-06-23? Type 'yes' or 'no'.
yes
```

The Agent keeps a small pending follow-up state:

```text
type: create_task_missing_title
due_date: optional ISO date
```

After the user answers, the Agent does not create the task immediately. It converts the answer into the existing pending confirmation flow.

### Why This Matters

This prevents two unsafe patterns:

```text
The Agent invents missing task details.
The Agent writes data without confirmation.
```

For now, this follow-up behavior is implemented in the local rule-based create flow. A later productization step can move the same idea into the unified Agent workflow so `ask-llm`, `ask-tools`, and normal natural-language input share one follow-up system.
