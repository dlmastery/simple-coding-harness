"""Step 1 - one round trip.

The smallest possible "coding agent": a system prompt, one user message,
one model reply. No tools, no loop, no memory. Everything later is built by
adding one thing at a time to this file.

Run:   python agent.py
Needs: BASE_URL, API_KEY and (optionally) MODEL in the environment.
"""

import os

from openai import OpenAI

SYSTEM_PROMPT = "You are a coding agent. Help the user with programming tasks."


def complete(messages):
    """Send the conversation to the model and return the assistant message."""
    client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4.1-mini"),
        messages=messages,
    )
    return response.choices[0].message


def main():
    user_input = input("you> ")
    message = complete([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])
    print(f"\nagent> {message.content}\n")


if __name__ == "__main__":
    main()
