import json
import uuid
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from db import client as db


def create_conversation() -> str:
    conv_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO conversations (id, started_at) VALUES (%s, NOW())",
        (conv_id,),
    )
    return conv_id


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    token_count: int | None = None,
    retrieved_chunks: list | None = None,
    langsmith_run_id: str | None = None,
) -> None:
    db.execute(
        """
        INSERT INTO messages
            (conversation_id, role, content, token_count, retrieved_chunks, langsmith_run_id, created_at)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, NOW())
        """,
        (
            conversation_id,
            role,
            content,
            token_count,
            json.dumps(retrieved_chunks or []),
            langsmith_run_id,
        ),
    )
    db.execute(
        "UPDATE conversations SET message_count = message_count + 1 WHERE id = %s",
        (conversation_id,),
    )


def load_history(conversation_id: str, limit: int = 20) -> List[BaseMessage]:
    rows = db.fetchall(
        """
        SELECT role, content FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (conversation_id, limit),
    )
    messages: List[BaseMessage] = []
    for row in rows:
        if row["role"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        elif row["role"] == "assistant":
            messages.append(AIMessage(content=row["content"]))
    return messages


def close_conversation(conversation_id: str, summary: str | None = None) -> None:
    db.execute(
        "UPDATE conversations SET ended_at = NOW(), summary = %s WHERE id = %s",
        (summary, conversation_id),
    )
