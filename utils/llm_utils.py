"""
Shared utilities for all agents.
- Singleton LLM instance (avoids 4 separate objects)
- Shared JSON parser (avoids copy-paste across 3 agent files)
"""
import json
import os
from langchain_groq import ChatGroq

_llm_instance = None

def get_llm(max_tokens: int = 2000, temperature: float = 0.0) -> ChatGroq:
    """
    Returns a shared ChatGroq instance.
    Created once on first call, reused after that.
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _llm_instance


def parse_json_response(text: str) -> list:
    """
    Safely parses LLM JSON output into a Python list.
    Handles markdown code fences, dict responses, and parse errors.
    """
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        last_fence = text.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            text = text[first_newline:last_fence].strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return [result]
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []