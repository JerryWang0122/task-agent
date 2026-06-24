# Phase 7: Productizing The Agent Workflow

## Step 7.1: Consolidate Agent Entrypoint

### Goal

In Phase 6, the Agent had several teaching entrypoints:

```text
tasks
overdue
weekly
ask-llm <message>
ask-tools <message>
rule-based natural-language routing
```

Those commands were useful because each one exposed one concept at a time.

In this step, we start turning the tutorial Agent into a product-style Agent by adding one normal natural-language entrypoint.

The user should be able to type:

```text
show overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
complete task 1
```

without choosing whether the implementation should use a local rule, JSON decision, or OpenAI tool-calling.

### Files We Touched

- `agent-python/main.py`: adds a unified message handler for normal user input.
- `agent-python/README.md`: documents the new primary interaction style.
- `docs/phase-7.md`: records the Phase 7 workflow direction.

### Concept

The important productization idea is this:

```text
The user should describe the goal.
The Agent runtime should choose the workflow path.
```

Phase 5 and Phase 6 intentionally exposed multiple internals:

```text
ask-llm     -> show explicit JSON decisions
ask-tools   -> show OpenAI automatic tool calling
tasks       -> show direct MCP tool execution
weekly      -> show Agent-side summarization
```

That is good for learning, but not ideal for product usage.

A product Agent should hide those internal choices behind one entrypoint:

```text
User message
  -> unified Agent handler
  -> deterministic workflow checks
  -> OpenAI tool-calling when available
  -> local fallback when OpenAI is not configured
  -> shared safety policy
  -> MCP tool execution
```

### Implementation

The Agent now has two important functions:

```python
handle_local_agent_message(user_message)
handle_agent_message(user_message)
```

`handle_local_agent_message` keeps the tutorial fallback rules in one function.

`handle_agent_message` is the new unified entrypoint for normal user messages.

Its flow is:

```text
1. Keep deterministic local handling for workflows that need special formatting or follow-up.
2. If OPENAI_API_KEY exists, use OpenAI tool-calling.
3. Apply the same Agent decision policy as before.
4. If OpenAI is not configured, use the local tutorial fallback.
```

This is a small but important architectural cleanup.

The CLI loop no longer owns all routing decisions directly. Instead, it delegates normal messages to the Agent runtime handler.

### Why We Keep Local Fallback

The local fallback remains useful for two reasons.

First, this is a tutorial project. You should still be able to run the Agent without an OpenAI API key.

Second, not every workflow should be blindly delegated to the LLM. Some behavior is deterministic runtime policy:

```text
group overdue tasks by priority
summarize weekly workload
ask a follow-up question when create_task is missing a title
```

These are examples of Agent orchestration, not backend business rules.

### How To Run Or Test

Start the Java backend first:

```bash
cd backend-java
JAVA_HOME="$(/usr/libexec/java_home -v 17)" mvn spring-boot:run
```

In another terminal, run the Agent:

```bash
cd agent-python
source .venv/bin/activate
export MCP_SERVER_PYTHON=../mcp-server/.venv/bin/python
python main.py
```

Try normal natural-language input:

```text
show overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
```

If `OPENAI_API_KEY` is set, normal messages can use OpenAI tool-calling automatically.

If `OPENAI_API_KEY` is not set, the Agent uses the local fallback rules.

### What You Learned

You learned the difference between a teaching CLI and a product Agent interface.

The user-facing interface should be simple:

```text
type a goal in natural language
```

The Agent runtime can still contain multiple internal strategies:

```text
deterministic workflow code
OpenAI tool-calling
local fallback rules
safety policy
MCP tool execution
```

### Next Step

Next, we can make the workflow state more explicit.

That means replacing scattered variables like:

```text
pending_action
pending_follow_up
```

with a clearer Agent workflow state object before introducing LangGraph.
