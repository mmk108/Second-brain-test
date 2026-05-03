import os
import tempfile

import chainlit as cl

from agents.graph import run_agent
from ingestion.embedder import ingest_document
from memory.conversation import (
    create_conversation,
    save_message,
    load_history,
    close_conversation,
)
from memory.user_profile import extract_and_store
from observability.langsmith import configure_tracing

configure_tracing()


@cl.on_chat_start
async def on_start():
    conv_id = create_conversation()
    cl.user_session.set("conversation_id", conv_id)
    await cl.Message(
        content="Hello! I'm your Second Brain assistant. Upload documents or ask me anything."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    conv_id: str = cl.user_session.get("conversation_id")

    # Handle file uploads
    if message.elements:
        for element in message.elements:
            if hasattr(element, "path") and element.path:
                filename = element.name
                file_type = os.path.splitext(filename)[1].lstrip(".").lower()
                status_msg = await cl.Message(content=f"Ingesting {filename}...").send()
                try:
                    doc_id = ingest_document(element.path, filename, file_type)
                    await cl.Message(content=f"Ingested **{filename}** (id: `{doc_id}`)").send()
                except Exception as exc:
                    await cl.Message(content=f"Failed to ingest {filename}: {exc}").send()

        if not message.content:
            return

    save_message(conv_id, "user", message.content)
    history = load_history(conv_id, limit=20)

    thinking_msg = cl.Message(content="")
    await thinking_msg.send()

    try:
        answer = await run_agent(message.content, history[:-1])  # exclude the message we just saved
    except Exception as exc:
        answer = f"Something went wrong: {exc}"

    thinking_msg.content = answer
    await thinking_msg.update()

    save_message(conv_id, "assistant", answer)


@cl.on_chat_end
async def on_end():
    conv_id: str = cl.user_session.get("conversation_id")
    if not conv_id:
        return

    history = load_history(conv_id, limit=50)
    await extract_and_store(history, conv_id)
    close_conversation(conv_id)
