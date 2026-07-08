import os

from config.settings import LANGCHAIN_API_KEY, LANGCHAIN_PROJECT, LANGCHAIN_TRACING_V2


def configure_tracing() -> None:
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
