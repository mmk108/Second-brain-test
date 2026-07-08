import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# OpenAI (embeddings only)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LangSmith
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "second-brain")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "second_brain")

# PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Authentication
BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME", "admin")
BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD", "")

# Azure (Phase 3)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "documents")

# Ingestion
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def validate_required() -> None:
    """Call at application startup to fail fast on missing required vars."""
    missing = [
        name for name, val in [
            ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
            ("DATABASE_URL", DATABASE_URL),
            ("BASIC_AUTH_PASSWORD", BASIC_AUTH_PASSWORD),
        ]
        if not val
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
