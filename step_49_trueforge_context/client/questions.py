"""Step 49 - The question loop: `tool.response_required` -> ask on the terminal -> `user.tool_response`.

Step 35 answered `ask_user` inside the tool call, in the same process.
Here the server pauses the turn, the client reads the question from the
pending call's arguments, asks, and resumes the session with the answer.
"""

from __future__ import annotations

from trueforge_sdk import TrueForge, UserMessage, UserToolResponseEvent

from . import context

ASK_USER = "ask_user_question"  # the built-in tool `config.ask_user_questions` turns on


def find_call(turn: context.Turn, ref: dict) -> dict | None:
    """The merged tool call a pending ref points at, through `source_event_id`."""
    message = turn.events.get(ref["source_event_id"])
    if not message or message.get("type") != "model.message":
        return None
    for call in message.get("tool_calls") or []:
        if call.get("id") == ref["id"]:
            return call
    return None


def questions(turn: context.Turn) -> list[dict]:
    """Every pending `ask_user_question` call: thread id, call id, question and options."""
    found = []
    for pending in turn.pending:
        for ref in pending["tool_calls"]:
            call = find_call(turn, ref)
            if not call or call.get("function", {}).get("name") != ASK_USER:
                continue
            arguments = context.arguments_of(call)
            found.append({
                "thread_id": pending["thread_id"],
                "tool_call_id": ref["id"],
                "question": arguments.get("question") or "",
                "options": list(arguments.get("options") or []),
            })
    return found


def ask(question: str, options: list[str], read=input) -> str:
    """Print the question with numbered options and return the chosen text.

    A number picks an option, as in step 35. Anything else is the answer as
    typed. An empty answer becomes a note the model can act on.
    """
    print(f"\n? {question}")
    for number, option in enumerate(options, 1):
        print(f"  {number}. {option}")
    answer = read("answer> ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer or "(no answer given)"


def answers(turn: context.Turn, read=input) -> list[UserToolResponseEvent]:
    """One `user.tool_response` per pending question, answered on the terminal."""
    return [
        UserToolResponseEvent(
            thread_id=q["thread_id"],
            tool_call_id=q["tool_call_id"],
            content=ask(q["question"], q["options"], read),
        )
        for q in questions(turn)
    ]


def run(client: TrueForge, session_id: str, prompt: str, read=input, on_delta=None) -> list[context.Turn]:
    """Send a prompt, answer every question the agent asks, return all the turns.

    The first turn carries the user message. Every turn that ends with
    pending questions is followed by a resume turn whose input is only the
    answers: the server refuses a turn that mixes the two.
    """
    turns = [context.stream_turn(client, session_id, [UserMessage(content=prompt)], on_delta)]
    while turns[-1].pending:
        replies = answers(turns[-1], read)
        if not replies:
            break  # pending calls that are not questions; nothing this client can answer
        turns.append(context.stream_turn(client, session_id, replies, on_delta))
    return turns
