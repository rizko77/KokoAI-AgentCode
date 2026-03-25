"""
KokoAI - OpenAI API Client
Supports: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
"""
import os

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return None
        _client = OpenAI(api_key=api_key)
        return _client
    except Exception:
        return None


def chat(
    prompt,
    model="gpt-4o-mini",
    system_prompt=None,
    temperature=0.7,
    max_tokens=2048,
):
    """Send a chat message to OpenAI. Returns None if not configured."""
    client = _get_client()
    if not client:
        return None

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def is_available():
    """Check if OpenAI API is configured."""
    return bool(os.getenv("OPENAI_API_KEY", ""))
