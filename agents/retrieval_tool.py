from langchain_core.tools import tool

from ingestion.embedder import get_vector_store


@tool
def retrieve_documents(query: str, k: int = 5) -> str:
    """Search the knowledge base for document chunks relevant to the query.

    Args:
        query: The search query.
        k: Number of results to return (default 5).

    Returns:
        Formatted string of relevant document excerpts.
    """
    store = get_vector_store()
    results = store.similarity_search(query, k=k)

    if not results:
        return "No relevant documents found."

    parts = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source_file") or doc.metadata.get("source_url", "unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content}")

    return "\n\n---\n\n".join(parts)
