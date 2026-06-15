# REFERENCE.md

# Personal Task Management Agent Tutorial Reference

## 1. Project Overview

This project is a tutorial-style implementation of a **Personal Task Management Agent**.

The goal is not only to build a working Agent, but to understand the architecture commonly used in enterprise Agent systems:

```text
User
  ↓
Python Agent
  ↓
MCP Client
  ↓
MCP Server
  ↓
Java Spring Boot API
  ↓
Database
```

The project uses a simple task-management domain because the data is easy to create and the behavior is easy to verify.

Example user requests:

```text
What tasks are due today?
Create a task to review the architecture document by Friday.
Mark the database migration task as completed.
Show overdue high-priority tasks.
```

## 2. Why This Project Is Useful

This project teaches the core concepts behind enterprise Agent development without requiring private company data.

It covers:

- Java backend API design
- Python Agent orchestration
- MCP tool design
- Tool calling
- Workflow design
- Safe Agent behavior
- Data ownership boundaries
- Gradual migration from normal APIs to AI-facing tools

The task-management domain is intentionally simple. This lets the learner focus on architecture instead of spending too much time on data preparation.

## 3. Main Architecture

```text
personal-task-agent/
├── backend-java/
│   ├── Spring Boot application
│   ├── Task REST API
│   ├── business logic
│   └── database access
│
├── mcp-server/
│   ├── MCP tool definitions
│   ├── tool input/output schemas
│   └── wrappers around backend APIs
│
├── agent-python/
│   ├── Agent loop
│   ├── LLM integration
│   ├── MCP client
│   └── natural-language workflows
│
├── docs/
│   ├── diagrams
│   └── learning notes
│
└── README.md
```

## 4. Responsibility Split

## 4.1 Java Backend

The Java backend represents the normal enterprise business system.

It owns:

- Task data model
- Business rules
- Persistence
- REST API
- Validation
- Security rules later

It should not depend on the Agent.

The backend should work even if the Agent does not exist.

Recommended API:

```text
GET    /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks
PATCH  /api/tasks/{id}/complete
DELETE /api/tasks/{id}
```

Recommended package structure:

```text
backend-java/src/main/java/com/example/taskagent/task/
├── Task.java
├── TaskStatus.java
├── TaskPriority.java
├── TaskRepository.java
├── TaskService.java
├── TaskController.java
└── dto/
    ├── CreateTaskRequest.java
    └── TaskResponse.java
```

Layer responsibilities:

| Layer | Responsibility |
|---|---|
| Controller | Handles HTTP requests and responses |
| Service | Contains business logic |
| Repository | Reads and writes data |
| Entity / Model | Represents task data |
| DTO | Defines API input and output shapes |

## 4.2 MCP Server

The MCP Server is the AI-facing tool layer.

It exposes selected backend capabilities as tools that an Agent can discover and call.

Example tools:

```text
list_tasks
get_task
create_task
complete_task
find_overdue_tasks
```

Each MCP tool should define:

- Tool name
- Tool description
- Input schema
- Output format
- Backend API call
- Error handling behavior

The MCP Server should not own business logic. It should delegate to the Java backend.

Example conceptual flow:

```text
Agent wants to list tasks
  ↓
Calls MCP tool: list_tasks
  ↓
MCP Server calls GET /api/tasks
  ↓
Java backend returns task data
  ↓
MCP Server returns structured result to Agent
```

## 4.3 Python Agent

The Python Agent is the orchestration layer.

It owns:

- Natural-language understanding
- Tool selection
- Tool calling
- Multi-step workflow
- Final response generation
- Safety checks before risky actions

It should not own:

- Database access
- Core business rules
- Task persistence
- Authorization rules

Conceptual flow:

```text
User: What tasks are due today?
  ↓
Agent decides it needs task data
  ↓
Agent calls list_tasks tool
  ↓
Tool returns tasks
  ↓
Agent filters or asks backend for due tasks
  ↓
Agent summarizes result
```

## 5. REST API vs MCP Tool

REST API is usually designed for software engineers and application clients.

MCP tools are designed for AI Agents.

| Topic | REST API | MCP Tool |
|---|---|---|
| Primary user | Developer / frontend / service | AI Agent |
| Interface | URL + HTTP method | Tool name + schema |
| Discovery | API docs / OpenAPI | Tool metadata |
| Agent friendliness | Medium | High |
| Business logic owner | Backend service | Backend service behind the tool |
| Example | `GET /api/tasks` | `list_tasks()` |

A good design often keeps both:

```text
Spring Boot Backend
├── REST API for normal applications
└── MCP Tools for AI Agents
```

Both should reuse the same service layer.

## 6. Data Model

Initial task model:

```text
Task
├── id
├── title
├── description
├── status
├── priority
├── dueDate
├── createdAt
└── updatedAt
```

Suggested status values:

```text
TODO
IN_PROGRESS
DONE
CANCELLED
```

Suggested priority values:

```text
LOW
MEDIUM
HIGH
URGENT
```

Minimal sample data:

```text
1. Prepare weekly report, HIGH, due today, TODO
2. Review Spring Boot API design, MEDIUM, due tomorrow, IN_PROGRESS
3. Pay electricity bill, HIGH, overdue, TODO
4. Read MCP documentation, MEDIUM, no due date, TODO
5. Clean completed tasks, LOW, due next week, TODO
```

## 7. Tutorial Roadmap

## Phase 0: Environment Setup

Goal:
Prepare tools and explain the project structure.

Topics:

- Java version
- Spring Boot
- Python version
- Package manager
- Local database
- OpenAI API key or compatible LLM provider
- MCP dependency

Expected output:

```text
Repository initialized
Java app can start
Python environment can run
```

## Phase 1: Build the Java Task API

Goal:
Create a normal backend service first.

Why:
In enterprise systems, the Agent usually does not own the business system. It calls existing services.

Tasks:

1. Create Spring Boot project
2. Define Task entity
3. Define TaskStatus and TaskPriority
4. Create repository
5. Create service
6. Create controller
7. Add DTOs
8. Add validation
9. Test with curl

Example API test:

```bash
curl http://localhost:8080/api/tasks
```

Expected learning:

- How the backend owns data and rules
- How REST APIs expose business capabilities
- Why Agent should not bypass backend logic

## Phase 2: Add Persistence and Seed Data

Goal:
Give the Agent real data to work with.

Recommended choices:

- H2 for easiest Java learning
- PostgreSQL later if desired

Tasks:

1. Add database dependency
2. Configure local database
3. Add sample tasks
4. Verify data through REST API

Expected learning:

- Why sample data is important for Agent testing
- How stable backend APIs make Agent development easier

## Phase 3: Build the MCP Server

Goal:
Expose backend capabilities as Agent-callable tools.

Tasks:

1. Create MCP server project
2. Define `list_tasks` tool
3. Define `get_task` tool
4. Define `create_task` tool
5. Define `complete_task` tool
6. Connect each tool to Java REST API
7. Test tools manually

Important design rule:

The MCP Server should call the Java API. It should not directly connect to the database.

Expected learning:

- MCP is a tool protocol, not a replacement for business services
- Tool metadata helps the Agent understand what it can do
- MCP creates a cleaner boundary between Agent and backend

## Phase 4: Build the Python Agent

Goal:
Create an Agent that can understand user intent and call MCP tools.

Start simple.

Do not begin with multi-agent architecture.

Tasks:

1. Create Python project
2. Add LLM client
3. Add MCP client
4. Register available tools
5. Implement simple Agent loop
6. Ask the Agent to list tasks
7. Ask the Agent to create a task
8. Ask the Agent to complete a task

Expected learning:

- What an Agent loop is
- How tool calling works
- How the Agent uses tool results to answer the user

## Phase 5: Add Workflow and Safety

Goal:
Prevent the Agent from making risky changes silently.

Task operations can be grouped by risk:

| Operation | Risk | Confirmation needed? |
|---|---:|---|
| List tasks | Low | No |
| Get task detail | Low | No |
| Create task | Medium | Usually yes |
| Complete task | Medium | Yes |
| Delete task | High | Always yes |

Tasks:

1. Add confirmation before create
2. Add confirmation before complete
3. Add confirmation before delete
4. Log every tool call
5. Return clear error messages

Expected learning:

- Enterprise Agents need guardrails
- Not every tool should be freely callable
- Human-in-the-loop is part of real Agent design

## Phase 6: Improve Agent Intelligence

Goal:
Make the Agent more useful without changing the backend too much.

Possible features:

- Show overdue tasks
- Summarize weekly workload
- Group tasks by priority
- Suggest what to work on next
- Convert vague dates such as "next Friday" into actual dates
- Ask follow-up questions when information is missing

Expected learning:

- The Agent can add intelligence on top of stable backend APIs
- Some logic belongs in backend, some in Agent orchestration

## Phase 7: Optional Enterprise Enhancements

These are optional after the core tutorial works.

Possible enhancements:

```text
Authentication
Authorization
Audit logs
OpenTelemetry tracing
LangSmith tracing
Vector search / RAG
Calendar integration
Email notification
Reminder service
Docker Compose
CI pipeline
```

## 8. Recommended Implementation Order

Use this order to avoid confusion:

```text
1. backend-java skeleton
2. task model
3. REST list/create APIs
4. local database and seed data
5. REST complete/delete APIs
6. MCP server skeleton
7. list_tasks MCP tool
8. create_task MCP tool
9. Python Agent skeleton
10. Agent calls list_tasks
11. Agent calls create_task
12. add confirmation rules
13. improve natural-language flows
```

## 9. Suggested Commands

These commands are examples. Adjust them based on the actual project setup.

Run Java backend:

```bash
cd backend-java
./mvnw spring-boot:run
```

Test Java API:

```bash
curl http://localhost:8080/api/tasks
```

Run MCP server:

```bash
cd mcp-server
python main.py
```

Run Python Agent:

```bash
cd agent-python
python main.py
```

## 10. Example Learning Conversation

A good tutorial interaction should look like this:

```text
Learner: Let's build the task API.
Mentor: Great. First we will build the Java backend because it represents the enterprise business system. The Agent should not own the task data directly. We will create the Task model, then expose it through a REST controller.
```

A poor interaction would look like this:

```text
Learner: Let's build the task API.
Assistant: Done. I generated all files.
```

The goal is understanding, not only completion.

## 11. Key Concepts to Explain During the Tutorial

## 11.1 Agent

An Agent is an LLM-driven workflow that can decide what tool to call and how to use the result.

Simple formula:

```text
Agent = LLM + instructions + tools + workflow + memory/safety
```

## 11.2 Tool

A tool is a callable function exposed to the Agent.

For this project:

```text
list_tasks
create_task
complete_task
```

## 11.3 MCP

MCP is a protocol that standardizes how tools and context are exposed to AI systems.

It helps avoid hard-coding every API detail inside the Agent.

## 11.4 Backend Service

The backend service owns the real business capability.

For this project, Java owns task management.

## 11.5 Separation of Concerns

The Agent decides what to do.

The backend decides what is valid.

The database stores state.

The MCP layer exposes backend capabilities safely.

## 12. Final Expected Result

At the end of the tutorial, the learner should be able to run a conversation like:

```text
User: What tasks are due today?
Agent: You have 2 tasks due today: prepare weekly report and pay electricity bill.

User: Add a task to review the MCP server code by Friday.
Agent: I can create that task. Please confirm.

User: Confirm.
Agent: Task created successfully.
```

## 13. Final Understanding Checklist

The learner should be able to answer:

- Why do we build the Java backend first?
- Why should the Python Agent not access the database directly?
- What does MCP add compared with REST?
- What is a tool schema?
- How does the Agent decide which tool to call?
- Which operations require human confirmation?
- How can this small project evolve into an enterprise Agent?

## 14. Recommended First Prompt to opencode

Use this prompt after placing `AGENTS.md` and `REFERENCE.md` in the repository root:

```text
Read AGENTS.md and REFERENCE.md first.

You are my mentor, not just a coding assistant.
Start with Phase 0 and guide me step by step to build the Personal Task Management Agent.
For each step, explain the goal, files, concepts, implementation, test command, and what I learned.
Do not generate the whole project at once.
```
