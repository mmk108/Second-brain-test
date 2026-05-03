import uuid
from datetime import datetime

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config.settings import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
)
from db import client as db

VECTOR_SIZE = 1536  # text-embedding-3-small


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)


def _ensure_collection(qdrant: QdrantClient) -> None:
    existing = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def get_vector_store() -> QdrantVectorStore:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    qdrant = _get_qdrant_client()
    _ensure_collection(qdrant)
    return QdrantVectorStore(
        client=qdrant,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )


def embed_and_store(chunks: list[Document], document_id: str) -> int:
    for chunk in chunks:
        chunk.metadata["document_id"] = document_id

    store = get_vector_store()
    store.add_documents(chunks)

    db.execute(
        "UPDATE documents SET chunk_count = %s, status = %s, updated_at = NOW() WHERE id = %s",
        (len(chunks), "complete", document_id),
    )
    return len(chunks)


def ingest_document(file_path: str, filename: str, file_type: str) -> str:
    from ingestion.loaders import load_file
    from ingestion.chunker import chunk_documents

    doc_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO documents (id, filename, file_type, status, created_at, updated_at)
        VALUES (%s, %s, %s, 'processing', NOW(), NOW())
        """,
        (doc_id, filename, file_type),
    )

    try:
        docs = load_file(file_path)
        chunks = chunk_documents(docs)
        embed_and_store(chunks, doc_id)
    except Exception as exc:
        db.execute(
            "UPDATE documents SET status = 'error', error_message = %s, updated_at = NOW() WHERE id = %s",
            (str(exc), doc_id),
        )
        raise

    return doc_id
