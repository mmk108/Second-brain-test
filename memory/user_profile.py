import json

from langchain_core.messages import BaseMessage

from db import client as db
from models.claude import get_llm

_EXTRACTION_PROMPT = """You are a memory extraction assistant. Review this conversation and extract key facts about the user.

Output a JSON array of objects with these fields:
- category: one of "preference", "fact", "style", "goal", "relationship"
- key: a short snake_case identifier (e.g. "communication_style", "name", "timezone")
- value: the extracted value as a string
- confidence: float 0.0–1.0

Only include facts that are clearly stated or strongly implied. Return an empty array [] if nothing notable.

Conversation:
{conversation}

Return only the JSON array, no other text."""


def get_profile() -> dict[str, str]:
    rows = db.fetchall("SELECT category, key, value FROM user_profile ORDER BY category, key")
    return {f"{r['category']}.{r['key']}": r["value"] for r in rows}


def format_profile_for_prompt() -> str:
    rows = db.fetchall("SELECT category, key, value FROM user_profile ORDER BY category, key")
    if not rows:
        return "No user profile facts stored yet."
    lines = [f"- [{r['category']}] {r['key']}: {r['value']}" for r in rows]
    return "\n".join(lines)


def upsert_fact(category: str, key: str, value: str, confidence: float = 1.0, conv_id: str | None = None) -> None:
    db.execute(
        """
        INSERT INTO user_profile (category, key, value, confidence, source_conv_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (category, key) DO UPDATE
            SET value = EXCLUDED.value,
                confidence = EXCLUDED.confidence,
                source_conv_id = EXCLUDED.source_conv_id,
                updated_at = NOW()
        """,
        (category, key, value, confidence, conv_id),
    )


def _strip_markdown_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` wrappers that Claude adds by default."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


async def extract_and_store(messages: list[BaseMessage], conversation_id: str) -> int:
    if not messages:
        return 0

    conversation_text = "\n".join(
        f"{m.__class__.__name__.replace('Message', '')}: {m.content}" for m in messages
    )
    prompt = _EXTRACTION_PROMPT.format(conversation=conversation_text)

    llm = get_llm(temperature=0.0, streaming=False)
    response = await llm.ainvoke(prompt)
    raw = _strip_markdown_fences(response.content)

    try:
        facts = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    for fact in facts:
        upsert_fact(
            category=fact.get("category", "fact"),
            key=fact.get("key", "unknown"),
            value=str(fact.get("value", "")),
            confidence=float(fact.get("confidence", 1.0)),
            conv_id=conversation_id,
        )
    return len(facts)
