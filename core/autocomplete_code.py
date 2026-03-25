"""
KokoAI - Smart Code Autocomplete Engine
Hybrid: Local N-gram Brain + AI Provider (Gemini/Claude) fallback
"""
import re
from pathlib import Path


# ── Language-specific boilerplate snippets ──────────────────────────
LANGUAGE_SNIPPETS = {
    "python": {
        "def ":      "def {name}({args}):\n    pass",
        "class ":    "class {name}:\n    def __init__(self):\n        pass",
        "if ":       "if {condition}:\n    pass",
        "for ":      "for {var} in {iterable}:\n    pass",
        "while ":    "while {condition}:\n    pass",
        "try":       "try:\n    pass\nexcept Exception as e:\n    print(e)",
        "import ":   "import {module}",
        "from ":     "from {module} import {name}",
        "with ":     "with open('{file}', 'r') as f:\n    content = f.read()",
        "print":     "print({value})",
        "lambda":    "lambda {args}: {expr}",
        "return":    "return {value}",
        "raise":     "raise {Exception}('{message}')",
        "assert":    "assert {condition}, '{message}'",
        "@":         "@staticmethod",
        "async def": "async def {name}({args}):\n    pass",
        "await":     "await {coroutine}",
        "__init__":  "def __init__(self):\n    pass",
        "main":      "if __name__ == '__main__':\n    main()",
    },
    "javascript": {
        "function ": "function {name}({args}) {\n    \n}",
        "const ":    "const {name} = {value};",
        "let ":      "let {name} = {value};",
        "var ":      "var {name} = {value};",
        "if ":       "if ({condition}) {\n    \n}",
        "for ":      "for (let i = 0; i < {n}; i++) {\n    \n}",
        "=>":        "({args}) => {\n    \n}",
        "async ":    "async function {name}() {\n    \n}",
        "await ":    "await {promise}",
        "class ":    "class {Name} {\n    constructor() {\n        \n    }\n}",
        "import ":   "import { {name} } from '{module}';",
        "export ":   "export default {name};",
        "console.":  "console.log({value});",
        "Promise":   "new Promise((resolve, reject) => {\n    \n});",
        "fetch":     "fetch('{url}')\n  .then(r => r.json())\n  .then(data => console.log(data))\n  .catch(err => console.error(err));",
    },
    "html": {
        "<!":        "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>",
        "<div":      "<div class=\"\">\n    \n</div>",
        "<form":     "<form action=\"\" method=\"post\">\n    <input type=\"text\" name=\"\" placeholder=\"\">\n    <button type=\"submit\">Submit</button>\n</form>",
        "<table":    "<table>\n    <thead>\n        <tr><th>Header</th></tr>\n    </thead>\n    <tbody>\n        <tr><td>Data</td></tr>\n    </tbody>\n</table>",
        "<nav":      "<nav>\n    <ul>\n        <li><a href=\"#\">Home</a></li>\n    </ul>\n</nav>",
        "<script":   "<script>\n    \n</script>",
        "<style":    "<style>\n    \n</style>",
        "<link":     "<link rel=\"stylesheet\" href=\"style.css\">",
        "<meta":     "<meta name=\"\" content=\"\">",
        "<img":      "<img src=\"\" alt=\"\" loading=\"lazy\">",
        "<button":   "<button type=\"button\" onclick=\"\">\n    Klik Saya\n</button>",
    },
    "css": {
        ".":         ".class-name {\n    \n}",
        "#":         "#id-name {\n    \n}",
        "@media":    "@media (max-width: 768px) {\n    \n}",
        "@keyframes":"@keyframes {name} {\n    from { }\n    to { }\n}",
        "body":      "body {\n    margin: 0;\n    padding: 0;\n    font-family: sans-serif;\n}",
        "flex":      "display: flex;\n    align-items: center;\n    justify-content: center;",
        "grid":      "display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));\n    gap: 1rem;",
    },
    "php": {
        "<?":        "<?php\n\n?>",
        "function ": "function {name}({args}) {\n    \n}",
        "class ":    "class {Name} {\n    public function __construct() {\n        \n    }\n}",
        "echo":      "echo \"{value}\";",
        "foreach":   "foreach (${array} as ${key} => ${value}) {\n    \n}",
    },
    "java": {
        "public class": "public class {Name} {\n    public static void main(String[] args) {\n        \n    }\n}",
        "public void":  "public void {name}() {\n    \n}",
        "System.out":   "System.out.println({value});",
        "for ":         "for (int i = 0; i < {n}; i++) {\n    \n}",
    },
}

# ── Common keyword completions per language ───────────────────────────
KEYWORD_COMPLETIONS = {
    "python": [
        "print(", "len(", "range(", "list(", "dict(", "set(", "tuple(",
        "str(", "int(", "float(", "bool(", "type(", "isinstance(",
        "open(", "enumerate(", "zip(", "map(", "filter(", "sorted(",
        "max(", "min(", "sum(", "abs(", "round(", "input(", "format(",
        "hasattr(", "getattr(", "setattr(", "delattr(", "dir(", "vars(",
        "super(", "property(", "staticmethod(", "classmethod(",
        "import os", "import sys", "import json", "import re",
        "import time", "import datetime", "import pathlib",
        "import requests", "import threading", "import logging",
        "from pathlib import Path", "from typing import List, Dict, Optional",
        "from dataclasses import dataclass", "from collections import defaultdict, Counter",
    ],
    "javascript": [
        "console.log(", "document.getElementById(", "document.querySelector(",
        "addEventListener(", "setTimeout(", "setInterval(", "clearTimeout(",
        "JSON.parse(", "JSON.stringify(", "Object.keys(", "Object.values(",
        "Array.from(", "Promise.all(", "Math.floor(", "Math.ceil(", "Math.round(",
        "localStorage.getItem(", "localStorage.setItem(", "fetch(",
        "require(", "module.exports", "const express = require('express')",
    ],
}


class AutocompleteEngine:
    """
    Hybrid autocomplete engine:
    1. Snippet-based: exact prefix match on language snippets
    2. N-gram: local brain predictions dari training data
    3. Keyword: common language keywords & stdlib patterns
    4. AI-powered: Gemini/Claude untuk complex completions
    """

    def __init__(self, brain=None, knowledge_base=None):
        self.brain = brain          # AIBrain instance
        self.knowledge = knowledge_base  # KnowledgeBase instance
        self._router = None         # lazy-loaded AI router

    def _get_router(self):
        if self._router is None:
            try:
                import sys, os
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from api.router import get_router
                self._router = get_router()
            except Exception:
                self._router = False
        return self._router if self._router else None

    def get_completions(self, code_context, language=None, max_results=8):
        """
        Main entry point: return list of (completion_text, score, source) tuples.
        """
        if not code_context or not code_context.strip():
            return []

        if language is None:
            language = self._detect_language(code_context)

        results = []

        # 1. Snippet completions (highest priority)
        snippets = self._snippet_completions(code_context, language)
        results.extend(snippets)

        # 2. N-gram local brain
        if self.brain:
            brain_results = self._brain_completions(code_context, language, max_results)
            results.extend(brain_results)

        # 3. Keyword completions
        kw_results = self._keyword_completions(code_context, language)
        results.extend(kw_results)

        # 4. Knowledge base snippets
        if self.knowledge:
            kb_results = self._knowledge_completions(code_context, language)
            results.extend(kb_results)

        # Deduplicate and sort by score
        seen = set()
        unique = []
        for text, score, source in sorted(results, key=lambda x: -x[1]):
            key = text.strip()[:40]
            if key not in seen and text.strip():
                seen.add(key)
                unique.append((text, score, source))

        return unique[:max_results]

    def get_ai_completion(self, code_context, language=None, instruction=""):
        """
        Use AI provider (Gemini/Claude) for complex completions.
        Falls back to local if no API key.
        """
        router = self._get_router()
        if not router:
            return None, "local"

        if language is None:
            language = self._detect_language(code_context)

        prompt = (
            f"Lanjutkan kode {language} berikut (berikan HANYA kode lanjutan, tanpa penjelasan):\n\n"
            f"```{language}\n{code_context}\n```"
        )
        if instruction:
            prompt += f"\n\nInstruksi tambahan: {instruction}"

        return router.chat(prompt, task_type="code")

    def get_line_completion(self, current_line, language=None):
        """Get completion for the current line being typed."""
        if not current_line.strip():
            return []

        if language is None:
            language = self._detect_language(current_line)

        results = []

        # Snippet match on current line
        snippets = self._snippet_completions(current_line, language, prefix_only=True)
        results.extend(snippets)

        # Keyword match
        results.extend(self._keyword_completions(current_line, language))

        # Brain line completion
        if self.brain:
            try:
                brain_lines = self.brain.predict_line(current_line, language)
                for text, score in brain_lines[:3]:
                    results.append((text, score * 0.9, "brain-line"))
            except Exception:
                pass

        seen, unique = set(), []
        for text, score, source in sorted(results, key=lambda x: -x[1]):
            key = text.strip()[:40]
            if key not in seen and text.strip():
                seen.add(key)
                unique.append((text, score, source))

        return unique[:5]

    # ── Private helpers ───────────────────────────────────────────────

    def _snippet_completions(self, code, language, prefix_only=False):
        """Match code snippets based on prefix trigger words."""
        results = []
        lang_snippets = LANGUAGE_SNIPPETS.get(language, {})
        code_stripped = code.strip()
        code_lower = code_stripped.lower()

        for trigger, template in lang_snippets.items():
            if code_lower.endswith(trigger.lower()) or code_lower == trigger.lower():
                results.append((template, 1.0, "snippet"))
            elif not prefix_only and code_lower.startswith(trigger.lower()):
                results.append((template, 0.8, "snippet"))

        return results

    def _brain_completions(self, code, language, max_results):
        """Use N-gram brain for token-level completions."""
        results = []
        try:
            predictions = self.brain.predict(code, max_results, language)
            for text, score in predictions:
                results.append((text, score, "brain"))
        except Exception:
            pass
        return results

    def _keyword_completions(self, code, language):
        """Match common keywords/stdlib functions."""
        results = []
        keywords = KEYWORD_COMPLETIONS.get(language, [])
        code_lower = code.lower().strip()
        last_word = code_lower.split()[-1] if code_lower.split() else ""

        for kw in keywords:
            if kw.lower().startswith(last_word) and last_word:
                score = len(last_word) / len(kw)
                results.append((kw, min(score + 0.3, 0.95), "keyword"))

        return results

    def _knowledge_completions(self, code, language):
        """Search knowledge base for relevant snippets."""
        results = []
        try:
            matches = self.knowledge.search_snippets(code, language)
            for score, lang, snippet in matches[:3]:
                code_text = snippet.get("code", "").strip()
                if code_text and len(code_text) < 500:
                    results.append((code_text, float(score) * 0.7, "knowledge"))
        except Exception:
            pass
        return results

    def _detect_language(self, code):
        """Detect programming language from code/file extension hint."""
        indicators = {
            "python": ["def ", "import ", "from ", "print(", "self.", "->", ":"],
            "javascript": ["function", "const ", "let ", "var ", "=>", "console.", "require("],
            "html": ["<!DOCTYPE", "<html", "<div", "<body", "<head", "</"],
            "css": ["{", "}", ":", "px", "em", "rem", "%", "@media"],
            "php": ["<?php", "echo ", "$", "->", "::"],
            "java": ["public class", "System.out", "import java"],
        }
        code_lower = code.lower()
        scores = {}
        for lang, hints in indicators.items():
            scores[lang] = sum(1 for h in hints if h.lower() in code_lower)
        if max(scores.values()) == 0:
            return "python"
        return max(scores, key=scores.get)

    def format_suggestions_display(self, completions):
        """Format completions for CLI display."""
        if not completions:
            return "Tidak ada suggestion."
        lines = []
        for i, (text, score, source) in enumerate(completions, 1):
            preview = text.replace("\n", " ").strip()[:60]
            lines.append(f"  [{i}] {preview}  [{source} {score:.0%}]")
        return "\n".join(lines)
