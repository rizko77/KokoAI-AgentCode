"""
KokoAI - Claude (Anthropic) API Client
Supports: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
"""
import os

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import anthropic
        api_key = os.getenv("CLAUDE_API_KEY", "")
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
        return _client
    except Exception:
        return None


def chat(
    prompt,
    model="claude-3-5-haiku-20241022",
    system_prompt=None,
    temperature=0.7,
    max_tokens=2048,
):
    """
    Send a chat message to Claude and return the response text.
    Returns None if API key is not set or request fails.
    """
    client = _get_client()
    if not client:
        return None

    try:
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception:
        return None


def generate_code(prompt, language="python", model="claude-3-5-haiku-20241022"):
    """Generate code using Claude."""
    system = (
        f"You are an expert {language} programmer. "
        f"Provide ONLY clean, safe, working {language} code without lengthy explanations. "
        "Use Indonesian language for any comments."
    )
    return chat(prompt, model=model, system_prompt=system, temperature=0.2)


def explain_code(code, language="python", model="claude-3-5-haiku-20241022"):
    """Explain code using Claude."""
    prompt = (
        f"Jelaskan kode {language} berikut dalam Bahasa Indonesia secara jelas:\n\n"
        f"```{language}\n{code}\n```"
    )
    return chat(prompt, model=model, temperature=0.4)


def answer_question(question, context="", model="claude-3-5-haiku-20241022"):
    """Answer a general question using Claude."""
    if context:
        prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}"
    else:
        prompt = question
    system = (
        "Kamu adalah KokoAI, asisten coding AI yang cerdas. "
        "Jawab dalam Bahasa Indonesia yang ringkas dan akurat."
    )
    return chat(prompt, model=model, system_prompt=system)


def is_available():
    """Check if Claude API is configured."""
    return bool(os.getenv("CLAUDE_API_KEY", ""))
