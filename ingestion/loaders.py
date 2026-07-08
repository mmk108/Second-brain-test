from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document


def load_file(file_path: str) -> list[Document]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
    elif suffix == ".docx":
        loader = Docx2txtLoader(file_path)
    elif suffix in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    docs = loader.load()
    for doc in docs:
        doc.metadata["source_file"] = path.name
        doc.metadata["file_type"] = suffix.lstrip(".")
    return docs


def load_url(url: str) -> list[Document]:
    loader = WebBaseLoader(url)
    docs = loader.load()
    for doc in docs:
        doc.metadata["source_url"] = url
        doc.metadata["file_type"] = "url"
    return docs
