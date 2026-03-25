import json
import time
from pathlib import Path
from collections import defaultdict


class KnowledgeBase:

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        self.code_snippets = defaultdict(list)
        self.patterns = defaultdict(list)
        self.documentation = {}
        self.search_cache = {}
        self.training_data = []
        self.metadata = {
            "created": time.time(),
            "last_updated": time.time(),
            "total_snippets": 0,
            "total_patterns": 0,
            "sources": [],
        }

        self.load()

    def load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.code_snippets = defaultdict(list, data.get("code_snippets", {}))
                self.patterns = defaultdict(list, data.get("patterns", {}))
                self.documentation = data.get("documentation", {})
                self.search_cache = data.get("search_cache", {})
                self.training_data = data.get("training_data", [])
                self.metadata = data.get("metadata", self.metadata)
            except (json.JSONDecodeError, Exception):
                pass

    def save(self):
        self.metadata["last_updated"] = time.time()
        self.metadata["total_snippets"] = sum(len(v) for v in self.code_snippets.values())
        self.metadata["total_patterns"] = sum(len(v) for v in self.patterns.values())

        data = {
            "code_snippets": dict(self.code_snippets),
            "patterns": dict(self.patterns),
            "documentation": self.documentation,
            "search_cache": self.search_cache,
            "training_data": self.training_data[-5000:],
            "metadata": self.metadata,
        }

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_snippet(self, language, code, source="local", tags=None):
        snippet = {
            "code": code,
            "source": source,
            "tags": tags or [],
            "timestamp": time.time(),
        }

        existing_codes = [s["code"] for s in self.code_snippets[language]]
        if code not in existing_codes:
            self.code_snippets[language].append(snippet)

            if len(self.code_snippets[language]) > 1000:
                self.code_snippets[language] = self.code_snippets[language][-1000:]

            if source not in self.metadata["sources"]:
                self.metadata["sources"].append(source)

    def add_pattern(self, name, example, language="python"):
        pattern = {
            "example": example,
            "language": language,
            "timestamp": time.time(),
        }

        key = f"{language}:{name}"
        existing = [p["example"] for p in self.patterns[key]]
        if example not in existing:
            self.patterns[key].append(pattern)
            if len(self.patterns[key]) > 100:
                self.patterns[key] = self.patterns[key][-100:]

    def add_documentation(self, topic, content):
        self.documentation[topic] = {
            "content": content,
            "timestamp": time.time(),
        }

    def add_training_data(self, input_tokens, output_tokens, language="python"):
        self.training_data.append({
            "input": input_tokens,
            "output": output_tokens,
            "language": language,
            "timestamp": time.time(),
        })

    def search_snippets(self, query, language=None, max_results=10):
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        languages = [language] if language else self.code_snippets.keys()

        for lang in languages:
            for snippet in self.code_snippets.get(lang, []):
                code_lower = snippet["code"].lower()
                score = sum(1 for word in query_words if word in code_lower)

                tag_score = sum(1 for word in query_words
                               if any(word in tag.lower() for tag in snippet.get("tags", [])))

                total_score = score + (tag_score * 2)

                if total_score > 0:
                    results.append((total_score, lang, snippet))

        results.sort(key=lambda x: x[0], reverse=True)
        return results[:max_results]

    def search_patterns(self, name, language=None):
        results = []
        for key, patterns in self.patterns.items():
            lang, pattern_name = key.split(":", 1) if ":" in key else ("unknown", key)
            if language and lang != language:
                continue
            if name.lower() in pattern_name.lower():
                results.extend(patterns)
        return results

    def get_training_data(self, language=None, limit=1000):
        data = self.training_data
        if language:
            data = [d for d in data if d.get("language") == language]
        return data[-limit:]

    def get_stats(self):
        return {
            "total_snippets": sum(len(v) for v in self.code_snippets.values()),
            "total_patterns": sum(len(v) for v in self.patterns.values()),
            "total_docs": len(self.documentation),
            "total_training": len(self.training_data),
            "languages": list(self.code_snippets.keys()),
            "sources": self.metadata.get("sources", []),
            "last_updated": self.metadata.get("last_updated", 0),
        }

    def clear_cache(self):
        self.search_cache = {}
        self.save()

    def export_for_training(self, language="python"):
        all_code = []
        for snippet in self.code_snippets.get(language, []):
            all_code.append(snippet["code"])

        for key, patterns in self.patterns.items():
            if key.startswith(f"{language}:"):
                for p in patterns:
                    all_code.append(p["example"])

        return "\n\n".join(all_code)
