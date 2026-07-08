from langchain_anthropic import ChatAnthropic
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def get_llm(temperature: float = 0.0, streaming: bool = True) -> ChatAnthropic:
    return ChatAnthropic(
        model=ANTHROPIC_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=temperature,
        streaming=streaming,
    )
