import asyncio
import json
import os
import re
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_DIR = PROJECT_ROOT / "mcp-server"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
AGENT_TOOL_NAMES = {"list_tasks", "get_task", "create_task", "complete_task"}


def decide_with_llm(user_message: str) -> dict[str, object]:
    """Ask OpenAI for a structured decision without executing any tool."""
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "action": "respond",
            "tool_name": None,
            "arguments": {},
            "requires_confirmation": False,
            "response": "OPENAI_API_KEY is not set. Export it before using ask-llm.",
        }

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the decision layer for a personal task Agent. "
                    "Return only JSON. Do not execute tools. "
                    "The action field must be exactly one of these two strings: "
                    "respond or call_tool. Never put a tool name in the action field. "
                    "Use this JSON shape: "
                    '{"action":"call_tool", "tool_name":"list_tasks", '
                    '"arguments":{}, "requires_confirmation":false, "response":null}. '
                    "Available tools are list_tasks, get_task, create_task, and complete_task. "
                    "When calling a tool, set action to call_tool and put the tool name in tool_name. "
                    "Set requires_confirmation to true for create_task and complete_task."
                ),
            },
            {"role": "user", "content": user_message},
        ],
    )

    content = response.choices[0].message.content or "{}"
    return normalize_llm_decision(json.loads(content))


async def decide_with_openai_tools(user_message: str) -> dict[str, object]:
    """Ask OpenAI to choose from MCP-derived tools using automatic tool calling."""
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "action": "respond",
            "tool_name": None,
            "arguments": {},
            "requires_confirmation": False,
            "response": "OPENAI_API_KEY is not set. Export it before using ask-tools.",
        }

    openai_tools = await get_openai_tools()
    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        tools=openai_tools,
        tool_choice="auto",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal task Agent. Use tools when task data is needed. "
                    "For create_task and complete_task, request the tool call; "
                    "the Agent runtime will ask the user for confirmation before execution."
                ),
            },
            {"role": "user", "content": user_message},
        ],
    )

    message = response.choices[0].message
    tool_calls = message.tool_calls or []
    if not tool_calls:
        return {
            "action": "respond",
            "tool_name": None,
            "arguments": {},
            "requires_confirmation": False,
            "response": message.content or "I do not have a response.",
        }

    tool_call = tool_calls[0]
    tool_name = tool_call.function.name
    raw_arguments = tool_call.function.arguments or "{}"
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {
            "action": "respond",
            "tool_name": None,
            "arguments": {},
            "requires_confirmation": False,
            "response": f"OpenAI returned invalid tool arguments: {raw_arguments}",
        }

    return normalize_llm_decision(
        {
            "action": "call_tool",
            "tool_name": tool_name,
            "arguments": arguments,
            "requires_confirmation": tool_name in {"create_task", "complete_task"},
            "response": None,
        }
    )


def normalize_llm_decision(decision: dict[str, object]) -> dict[str, object]:
    """Normalize common LLM decision shape mistakes before policy execution."""
    known_tools = {"list_tasks", "get_task", "create_task", "complete_task"}
    action = decision.get("action")

    if action in known_tools:
        decision["tool_name"] = decision.get("tool_name") or action
        decision["action"] = "call_tool"

    decision.setdefault("arguments", {})
    decision.setdefault("requires_confirmation", decision.get("tool_name") in {"create_task", "complete_task"})
    decision.setdefault("response", None)

    return decision


def format_decision(decision: dict[str, object]) -> str:
    """Return a readable JSON representation of an LLM decision."""
    return json.dumps(decision, indent=2)


def mcp_tool_to_openai_tool(tool: object) -> dict[str, object]:
    """Convert one MCP tool definition into OpenAI's function tool shape."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }


async def execute_llm_decision(decision: dict[str, object]) -> str:
    """Execute read-only LLM decisions through MCP tools."""
    action = decision.get("action")
    if action == "respond":
        return str(decision.get("response") or "I do not have a response.")

    if action != "call_tool":
        return f"Unsupported LLM action: {action}"

    tool_name = decision.get("tool_name")
    arguments = decision.get("arguments") or {}
    if not isinstance(arguments, dict):
        return "Invalid LLM decision: arguments must be an object."

    if tool_name == "list_tasks":
        return await list_tasks()

    if tool_name == "get_task":
        task_id = arguments.get("task_id")
        if task_id is None:
            return "Invalid LLM decision: get_task requires task_id."

        return await get_task(int(task_id))

    if tool_name in {"create_task", "complete_task"}:
        return f"LLM suggested write tool {tool_name}. Confirmation flow will be added next."

    return f"Unsupported LLM tool: {tool_name}"


def pending_action_from_llm_decision(decision: dict[str, object]) -> tuple[dict[str, object], str] | None:
    """Convert an LLM write-tool decision into a pending confirmation action."""
    if decision.get("action") != "call_tool":
        return None

    arguments = decision.get("arguments") or {}
    if not isinstance(arguments, dict):
        return None

    tool_name = decision.get("tool_name")
    if tool_name == "complete_task":
        task_id = arguments.get("task_id")
        if task_id is None:
            return None

        return (
            {"type": "complete_task", "task_id": int(task_id)},
            f"Confirm: mark task #{task_id} as completed? Type 'yes' or 'no'.",
        )

    if tool_name == "create_task":
        title = arguments.get("title")
        if not title:
            return None

        return (
            {"type": "create_task", "title": str(title)},
            f"Confirm: create task '{title}'? Type 'yes' or 'no'.",
        )

    return None


async def list_mcp_tools() -> str:
    """Start the MCP Server and return its available tool metadata."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()

            lines = ["Available MCP tools:"]
            for tool in tools.tools:
                lines.append(f"- {tool.name}: {tool.description}")

            return "\n".join(lines)


async def get_openai_tools() -> list[dict[str, object]]:
    """Return selected MCP tools converted into OpenAI function tool definitions."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            return [
                mcp_tool_to_openai_tool(tool)
                for tool in tools.tools
                if tool.name in AGENT_TOOL_NAMES
            ]


async def list_openai_tools() -> str:
    """Return MCP tools converted into OpenAI function tool definitions."""
    return json.dumps(await get_openai_tools(), indent=2)


async def list_tasks() -> str:
    """Call the MCP list_tasks tool and format the result for the user."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", arguments={})

            structured_content = result.structuredContent or {}
            tasks = structured_content.get("result")
            if tasks is None:
                tasks = [json.loads(content.text) for content in result.content]

            if not tasks:
                return "No tasks found."

            lines = ["Tasks from the Java backend:"]
            for task in tasks:
                due_date = task.get("dueDate") or "no due date"
                lines.append(
                    f"- #{task['id']} {task['title']} "
                    f"[{task['status']}, {task['priority']}, due: {due_date}]"
                )

            return "\n".join(lines)


async def get_task(task_id: int) -> str:
    """Call the MCP get_task tool and format one task for the user."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_task", arguments={"task_id": task_id})

            structured_content = result.structuredContent or {}
            task = structured_content.get("result")
            if task is None:
                task = json.loads(result.content[0].text)

            due_date = task.get("dueDate") or "no due date"
            description = task.get("description") or "no description"
            return (
                f"Task #{task['id']}: {task['title']}\n"
                f"Status: {task['status']}\n"
                f"Priority: {task['priority']}\n"
                f"Due date: {due_date}\n"
                f"Description: {description}"
            )


async def complete_task(task_id: int) -> str:
    """Call the MCP complete_task tool after the user confirms the action."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("complete_task", arguments={"task_id": task_id})

            structured_content = result.structuredContent or {}
            task = structured_content.get("result")
            if task is None:
                task = json.loads(result.content[0].text)

            return f"Completed task #{task['id']}: {task['title']}"


async def create_task(title: str) -> str:
    """Call the MCP create_task tool after the user confirms the action."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("create_task", arguments={"title": title})

            structured_content = result.structuredContent or {}
            task = structured_content.get("result")
            if task is None:
                task = json.loads(result.content[0].text)

            return f"Created task #{task['id']}: {task['title']}"


def extract_create_task_title(user_message: str) -> str | None:
    """Extract a title from simple phrases like 'create task Buy milk'."""
    match = re.search(r"^(?:create|add)\s+(?:a\s+)?task\s+(.+)$", user_message, re.IGNORECASE)
    if not match:
        return None

    title = match.group(1).strip()
    if not title:
        return None

    return title


def extract_task_id(user_message: str) -> int | None:
    """Extract a task id from simple phrases like 'task 1' or '#1'."""
    match = re.search(r"(?:task\s*#?|#)(\d+)", user_message.lower())
    if not match:
        return None

    return int(match.group(1))


def should_complete_task(user_message: str) -> bool:
    """Return True when the user is asking to mark a task complete."""
    normalized_message = user_message.lower()
    complete_words = {"complete", "completed", "finish", "finished", "done"}

    return extract_task_id(normalized_message) is not None and any(
        word in normalized_message for word in complete_words
    )


def should_list_tasks(user_message: str) -> bool:
    """Return True when the user is asking to see task records."""
    normalized_message = user_message.lower()
    task_words = {"task", "tasks", "todo", "todos"}
    list_words = {"show", "list", "see", "view", "display", "what"}

    return any(word in normalized_message for word in task_words) and any(
        word in normalized_message for word in list_words
    )


def answer(user_message: str) -> str:
    """Return a placeholder response until MCP and LLM integration are added."""
    return (
        "Agent skeleton received your message: "
        f"{user_message}\n"
        "MCP tool calling will be added in the next steps."
    )


def main() -> None:
    print("Personal Task Agent")
    print(
        "Type a task question, 'tools', 'openai-tools', 'tasks', "
        "'ask-llm <message>', 'ask-tools <message>', or 'exit' to quit."
    )
    pending_action: dict[str, object] | None = None

    while True:
        user_message = input("> ").strip()
        normalized_message = user_message.lower()

        if normalized_message in {"exit", "quit"}:
            print("Goodbye.")
            return

        if not user_message:
            continue

        if pending_action is not None:
            if normalized_message in {"yes", "y", "confirm"}:
                action_type = pending_action["type"]

                if action_type == "complete_task":
                    task_id = int(pending_action["task_id"])
                    pending_action = None
                    print(asyncio.run(complete_task(task_id)))
                    continue

                if action_type == "create_task":
                    title = str(pending_action["title"])
                    pending_action = None
                    print(asyncio.run(create_task(title)))
                    continue

                pending_action = None
                print("Cancelled unknown pending action.")
                continue

            if normalized_message in {"no", "n", "cancel"}:
                pending_action = None
                print("Cancelled. No task was changed.")
                continue

            print("Please answer 'yes' to confirm or 'no' to cancel.")
            continue

        if normalized_message == "tools":
            print(asyncio.run(list_mcp_tools()))
            continue

        if normalized_message == "openai-tools":
            print(asyncio.run(list_openai_tools()))
            continue

        if normalized_message.startswith("ask-llm "):
            llm_message = user_message[len("ask-llm ") :].strip()
            if not llm_message:
                print("Please provide a message after ask-llm.")
                continue

            decision = decide_with_llm(llm_message)
            print("LLM decision:")
            print(format_decision(decision))

            pending_llm_action = pending_action_from_llm_decision(decision)
            if pending_llm_action is not None:
                pending_action, confirmation_message = pending_llm_action
                print("Agent result:")
                print(confirmation_message)
                continue

            print("Agent result:")
            print(asyncio.run(execute_llm_decision(decision)))
            continue

        if normalized_message.startswith("ask-tools "):
            tool_message = user_message[len("ask-tools ") :].strip()
            if not tool_message:
                print("Please provide a message after ask-tools.")
                continue

            decision = asyncio.run(decide_with_openai_tools(tool_message))
            print("OpenAI tool decision:")
            print(format_decision(decision))

            pending_tool_action = pending_action_from_llm_decision(decision)
            if pending_tool_action is not None:
                pending_action, confirmation_message = pending_tool_action
                print("Agent result:")
                print(confirmation_message)
                continue

            print("Agent result:")
            print(asyncio.run(execute_llm_decision(decision)))
            continue

        if normalized_message == "tasks":
            print(asyncio.run(list_tasks()))
            continue

        if should_complete_task(user_message):
            task_id = extract_task_id(user_message)
            pending_action = {"type": "complete_task", "task_id": task_id}
            print(f"Confirm: mark task #{task_id} as completed? Type 'yes' or 'no'.")
            continue

        create_title = extract_create_task_title(user_message)
        if create_title is not None:
            pending_action = {"type": "create_task", "title": create_title}
            print(f"Confirm: create task '{create_title}'? Type 'yes' or 'no'.")
            continue

        task_id = extract_task_id(user_message)
        if task_id is not None:
            print(asyncio.run(get_task(task_id)))
            continue

        if should_list_tasks(user_message):
            print(asyncio.run(list_tasks()))
            continue

        print(answer(user_message))


if __name__ == "__main__":
    main()
