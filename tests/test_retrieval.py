from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


def test_retrieve_documents_formats_output():
    mock_doc = Document(
        page_content="This is relevant content.",
        metadata={"source_file": "test.pdf"},
    )
    with patch("agents.retrieval_tool.get_vector_store") as mock_store_fn:
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = [mock_doc]
        mock_store_fn.return_value = mock_store

        from agents.retrieval_tool import retrieve_documents

        result = retrieve_documents.invoke({"query": "test query", "k": 1})

    assert "test.pdf" in result
    assert "This is relevant content." in result


def test_retrieve_documents_no_results():
    with patch("agents.retrieval_tool.get_vector_store") as mock_store_fn:
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = []
        mock_store_fn.return_value = mock_store

        from agents.retrieval_tool import retrieve_documents

        result = retrieve_documents.invoke({"query": "nothing here", "k": 5})

    assert "No relevant documents found" in result
