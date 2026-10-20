from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.constants import SAFETY_NOTE


def build_review_input(messages) -> str:
    question, turn = "", []

    for message in reversed(messages[:-1]):
        if isinstance(message, HumanMessage):
            question = message.text
            break
        turn.append(message)
    turn.reverse()

    # Show each tool call's arguments next to its result, so the verifier can see what was searched for.
    tool_args = {call["id"]: call["args"] for m in turn if isinstance(m, AIMessage) for call in m.tool_calls}
    evidence = [
        f"[{m.name} {tool_args.get(m.tool_call_id, {})}] {m.text}"
        for m in turn if isinstance(m, ToolMessage)
    ]
    draft = messages[-1].text
    if evidence:
        evidence_text = "\n\n".join(evidence)
    else:
        evidence_text = "No tools were used"
    return f"USER QUESTION:\n{question}\n\nEVIDENCE FROM TOOLS:\n{evidence_text}\n\nDRAFT ANSWER:\n{draft}"


def with_safety_note(draft: AIMessage) -> AIMessage:
    """Same id as the draft, so it replaces the draft in the state instead of being added."""
    return AIMessage(content=draft.text + SAFETY_NOTE, id=draft.id)
