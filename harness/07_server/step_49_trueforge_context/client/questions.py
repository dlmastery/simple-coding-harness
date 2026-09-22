"""Step 49 - The question loop: `tool.response_required` -> ask on the terminal -> `user.tool_response`.

Step 35 answered `ask_user` inside the tool call, in the same process.
Here the server pauses the turn, the client reads the question from the
pending call's arguments, asks, and resumes the session with the answer.
"""

from __future__ import annotations

from trueforge_sdk import TrueForge, UserMessage, UserToolResponseEvent

from . import context

ASK_USER = "ask_user_question"  # the built-in tool `config.ask_user_questions` turns on
MAX_ROUNDS = 20  # resume turns one run() may make; a server that keeps asking cannot loop forever
NO_ANSWER = "(no answer given)"


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
    try:
        answer = read("answer> ").strip()
    except (EOFError, KeyboardInterrupt):  # stdin closed or ctrl-c: the model gets a note, not a crash
        print()
        return NO_ANSWER
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer or NO_ANSWER


def unanswerable(turn: context.Turn) -> list[dict]:
    """Pending calls that are not questions: client-side tools this client does not implement."""
    found = []
    for pending in turn.pending:
        for ref in pending["tool_calls"]:
            call = find_call(turn, ref)
            name = (call or {}).get("function", {}).get("name") or "?"
            if name != ASK_USER:
                found.append({"thread_id": pending["thread_id"], "tool_call_id": ref["id"], "name": name})
    return found


def answers(turn: context.Turn, read=input) -> list[UserToolResponseEvent]:
    """One `user.tool_response` per pending call: questions answered on the terminal, anything else declined."""
    replies = [
        UserToolResponseEvent(
            thread_id=q["thread_id"],
            tool_call_id=q["tool_call_id"],
            content=ask(q["question"], q["options"], read),
        )
        for q in questions(turn)
    ]
    for call in unanswerable(turn):  # every pending call must get a response or the turn stays paused
        replies.append(UserToolResponseEvent(
            thread_id=call["thread_id"], tool_call_id=call["tool_call_id"],
            content=f"Error: this client cannot run {call['name']}",
        ))
    return replies


def run(client: TrueForge, session_id: str, prompt: str, read=input, on_delta=None) -> list[context.Turn]:
    """Send a prompt, answer every question the agent asks, return all the turns.

    The first turn carries the user message. Every `done` turn that ends
    with pending calls is followed by a resume turn whose input is only the
    answers: the server refuses a turn that mixes the two. A turn that
    ended in `error` or `cancelled` is not resumed, whatever it left
    pending, and `MAX_ROUNDS` bounds the number of resumes.
    """
    turns = [context.stream_turn(client, session_id, [UserMessage(content=prompt)], on_delta)]
    for _round in range(MAX_ROUNDS):
        if turns[-1].status != "done" or not turns[-1].pending:
            return turns
        turns.append(context.stream_turn(client, session_id, answers(turns[-1], read), on_delta))
    turns[-1].state = {"status": "error", "message": f"still asking after {MAX_ROUNDS} resume turns"}
    return turns
