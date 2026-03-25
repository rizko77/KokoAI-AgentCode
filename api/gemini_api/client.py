"""
KokoAI - Gemini API Client
Supports: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
"""
import os

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception:
        return None


def chat(
    prompt,
    model="gemini-2.0-flash",
    system_prompt=None,
    temperature=0.7,
    max_tokens=2048,
):
    """
    Send a chat message to Gemini and return the response text.
    Returns None if API key is not set or request fails.
    """
    client = _get_client()
    if not client:
        return None

    try:
        from google.genai import types

        contents = []
        if system_prompt:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=system_prompt)],
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text="Siap! Saya akan membantu.")],
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )
        )

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        return response.text
    except Exception as e:
        return None


def generate_code(prompt, language="python", model="gemini-2.0-flash"):
    """Generate code using Gemini."""
    system = (
        f"Kamu adalah expert programmer {language}. "
        f"Berikan HANYA kode {language} yang diminta tanpa penjelasan panjang. "
        "Pastikan kode bersih, aman, dan siap digunakan."
    )
    return chat(prompt, model=model, system_prompt=system, temperature=0.3)


def explain_code(code, language="python", model="gemini-2.0-flash"):
    """Explain code using Gemini."""
    prompt = f"Jelaskan kode {language} berikut secara singkat dan jelas:\n\n```{language}\n{code}\n```"
    return chat(prompt, model=model, temperature=0.5)


def answer_question(question, context="", model="gemini-2.0-flash"):
    """Answer a general question using Gemini."""
    if context:
        prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}"
    else:
        prompt = question
    system = (
        "Kamu adalah KokoAI, asisten coding AI lokal yang pintar. "
        "Jawab dalam Bahasa Indonesia yang jelas dan padat. "
        "Jika tentang coding, berikan contoh kode yang relevan."
    )
    return chat(prompt, model=model, system_prompt=system)


def is_available():
    """Check if Gemini API is configured."""
    return bool(os.getenv("GEMINI_API_KEY", ""))
