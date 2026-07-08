from langchain_core.tools import tool

from memory.user_profile import format_profile_for_prompt, upsert_fact


@tool
def read_user_profile() -> str:
    """Read the current user profile — known facts, preferences, and style notes."""
    return format_profile_for_prompt()


@tool
def update_user_profile(category: str, key: str, value: str) -> str:
    """Store or update a fact about the user in their profile.

    Args:
        category: One of preference, fact, style, goal, relationship.
        key: Short snake_case identifier (e.g. communication_style, name, timezone).
        value: The value to store.
    """
    upsert_fact(category=category, key=key, value=value)
    return f"Stored: [{category}] {key} = {value}"
