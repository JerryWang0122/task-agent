def answer(user_message: str) -> str:
    """Return a placeholder response until MCP and LLM integration are added."""
    return (
        "Agent skeleton received your message: "
        f"{user_message}\n"
        "MCP tool calling will be added in the next steps."
    )


def main() -> None:
    print("Personal Task Agent")
    print("Type a task question. Type 'exit' to quit.")

    while True:
        user_message = input("> ").strip()

        if user_message.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return

        if not user_message:
            continue

        print(answer(user_message))


if __name__ == "__main__":
    main()
