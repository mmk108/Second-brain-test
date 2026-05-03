import os

import pytest

# Patch required env vars before any project imports so config/settings.py
# does not crash during test collection.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_second_brain")
os.environ.setdefault("LANGCHAIN_API_KEY", "test-langsmith-key")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("BASIC_AUTH_USERNAME", "test")
os.environ.setdefault("BASIC_AUTH_PASSWORD", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")


@pytest.fixture
def sample_txt(tmp_path) -> str:
    """A small plain-text file for ingestion tests."""
    f = tmp_path / "sample.txt"
    f.write_text(
        "Artificial intelligence is the simulation of human intelligence by machines. "
        "Machine learning is a subset of AI that allows systems to learn from data. "
        "Deep learning uses neural networks with many layers to model complex patterns."
    )
    return str(f)


@pytest.fixture
def sample_md(tmp_path) -> str:
    """A markdown file treated as plain text."""
    f = tmp_path / "notes.md"
    f.write_text("# Project Notes\n\nThis document covers the Q3 roadmap.\n\n- Feature A\n- Feature B\n")
    return str(f)


@pytest.fixture
def long_txt(tmp_path) -> str:
    """A text file long enough to produce multiple chunks."""
    f = tmp_path / "long.txt"
    f.write_text(("word " * 300 + "\n") * 10)
    return str(f)
