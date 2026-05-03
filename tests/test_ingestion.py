import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from ingestion.chunker import chunk_documents
from ingestion.loaders import load_file


def test_chunk_documents_splits_large_text():
    doc = Document(page_content="word " * 500, metadata={})
    chunks = chunk_documents([doc])
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= 1200  # some slack over CHUNK_SIZE


def test_chunk_documents_adds_chunk_index():
    doc = Document(page_content="word " * 500, metadata={})
    chunks = chunk_documents([doc])
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i


def test_load_txt_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Hello world.\nThis is a test document.")
        path = f.name
    try:
        docs = load_file(path)
        assert len(docs) >= 1
        assert "Hello world" in docs[0].page_content
        assert docs[0].metadata["file_type"] == "txt"
    finally:
        os.unlink(path)


def test_load_unsupported_raises():
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_file("/tmp/test.xyz")
