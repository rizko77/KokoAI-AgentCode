import json
import math
import time
import random
from collections import Counter, defaultdict
from pathlib import Path


class AIBrain:

    def __init__(self, tokenizer, knowledge_base, model_path=None, ngram_size=3):
        self.tokenizer = tokenizer
        self.knowledge = knowledge_base
        self.model_path = Path(model_path) if model_path else None
        self.ngram_size = ngram_size

        self.ngrams = defaultdict(Counter)
        self.transitions = defaultdict(Counter)
        self.document_freq = Counter()
        self.total_documents = 0
        self.total_tokens_trained = 0
        self.training_sessions = 0
        self.last_trained = 0
        self.accuracy_log = []
        self.line_patterns = defaultdict(Counter)
        self.block_patterns = defaultdict(Counter)

        self.load_model()

    def train(self, code, language="python"):
        if not code or not code.strip():
            return

        tokens = self.tokenizer.tokenize(code, language)
        if len(tokens) < self.ngram_size:
            return

        self.tokenizer.build_vocab(tokens)

        for i in range(len(tokens) - self.ngram_size):
            context = tuple(tokens[i:i + self.ngram_size - 1])
            target = tokens[i + self.ngram_size - 1]
            self.ngrams[context][target] += 1

        for i in range(len(tokens) - 1):
            current = tokens[i]
            next_token = tokens[i + 1]
            self.transitions[current][next_token] += 1

        lines = code.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            words = stripped.split()
            if len(words) >= 2:
                prefix = words[0]
                completion = " ".join(words[1:])
                self.line_patterns[prefix][completion] += 1

            if len(words) >= 3:
                prefix2 = " ".join(words[:2])
                completion2 = " ".join(words[2:])
                self.line_patterns[prefix2][completion2] += 1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.endswith(":") and i + 1 < len(lines):
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line:
                    self.block_patterns[stripped][next_line] += 1

        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.document_freq[token] += 1
        self.total_documents += 1

        self.total_tokens_trained += len(tokens)
        self.last_trained = time.time()

        self.knowledge.add_training_data(
            tokens[:self.ngram_size],
            tokens[self.ngram_size:self.ngram_size + 5],
            language
        )

    def predict(self, context_code, max_suggestions=5, language="python"):
        if not context_code:
            return []

        suggestions = []

        tokens = self.tokenizer.tokenize(context_code, language)
        if len(tokens) >= self.ngram_size - 1:
            context = tuple(tokens[-(self.ngram_size - 1):])
            if context in self.ngrams:
                candidates = self.ngrams[context]
                total = sum(candidates.values())
                for token, count in candidates.most_common(max_suggestions * 2):
                    prob = count / total
                    suggestions.append((token, prob, "ngram"))

        if tokens:
            last_token = tokens[-1]
            if last_token in self.transitions:
                candidates = self.transitions[last_token]
                total = sum(candidates.values())
                for token, count in candidates.most_common(max_suggestions * 2):
                    prob = count / total
                    suggestions.append((token, prob * 0.8, "markov"))

        current_line = context_code.split("\n")[-1].strip()
        if current_line:
            words = current_line.split()
            for prefix_len in range(min(3, len(words)), 0, -1):
                prefix = " ".join(words[:prefix_len])
                if prefix in self.line_patterns:
                    candidates = self.line_patterns[prefix]
                    total = sum(candidates.values())
                    for completion, count in candidates.most_common(max_suggestions):
                        prob = count / total
                        suggestions.append((completion, prob * 0.9, "line_pattern"))
                    break

        lines = context_code.split("\n")
        for line in reversed(lines[-5:]):
            stripped = line.strip()
            if stripped.endswith(":") and stripped in self.block_patterns:
                candidates = self.block_patterns[stripped]
                total = sum(candidates.values())
                for completion, count in candidates.most_common(3):
                    prob = count / total
                    suggestions.append((completion, prob * 0.7, "block"))
                break

        return self._rank_suggestions(suggestions, tokens, max_suggestions)

    def predict_line(self, context_code, language="python"):
        suggestions = []

        lines = context_code.split("\n")
        current_line = lines[-1] if lines else ""
        prev_lines = lines[-5:-1] if len(lines) > 1 else []

        for line in reversed(prev_lines + [current_line]):
            stripped = line.strip()
            if stripped in self.block_patterns:
                candidates = self.block_patterns[stripped]
                total = sum(candidates.values())
                for completion, count in candidates.most_common(5):
                    prob = count / total
                    suggestions.append((completion, prob))

        token_suggestions = self.predict(context_code, max_suggestions=10, language=language)

        if token_suggestions:
            line = " ".join([s[0] for s in token_suggestions[:8]])
            if line:
                suggestions.append((line, token_suggestions[0][1] * 0.5))

        if current_line.strip():
            words = current_line.strip().split()
            prefix = words[0] if words else ""
            if prefix in self.line_patterns:
                candidates = self.line_patterns[prefix]
                total = sum(candidates.values())
                for completion, count in candidates.most_common(3):
                    prob = count / total
                    full_line = f"{prefix} {completion}"
                    suggestions.append((full_line, prob))

        seen = set()
        unique = []
        for text, score in suggestions:
            if text not in seen:
                seen.add(text)
                unique.append((text, score))

        unique.sort(key=lambda x: x[1], reverse=True)
        return unique[:5]

    def _rank_suggestions(self, suggestions, context_tokens, max_results):
        if not suggestions:
            return []

        scored = {}

        for token, prob, source in suggestions:
            score = prob
            idf = self._calculate_idf(token)
            score *= (1 + idf * 0.1)

            if token in context_tokens:
                score *= 1.2

            source_weights = {
                "ngram": 1.0,
                "line_pattern": 0.95,
                "markov": 0.8,
                "block": 0.7,
            }
            score *= source_weights.get(source, 0.5)

            if token not in scored or score > scored[token]:
                scored[token] = score

        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
        return ranked[:max_results]

    def _calculate_idf(self, token):
        if self.total_documents == 0 or token not in self.document_freq:
            return 0
        return math.log(self.total_documents / (1 + self.document_freq[token]))

    def train_from_file(self, filepath, language=None):
        filepath = Path(filepath)
        if not filepath.exists():
            return False

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            return False

        if not code.strip():
            return False

        if language is None:
            from config.settings import SUPPORTED_EXTENSIONS
            ext = filepath.suffix.lower()
            language = SUPPORTED_EXTENSIONS.get(ext, "python")

        self.train(code, language)
        self.knowledge.add_snippet(language, code, source=str(filepath))

        return True

    def train_from_directory(self, directory, recursive=True):
        from config.settings import SUPPORTED_EXTENSIONS

        directory = Path(directory)
        if not directory.exists():
            return 0

        count = 0
        pattern = "**/*" if recursive else "*"

        for filepath in directory.glob(pattern):
            if filepath.is_file() and filepath.suffix.lower() in SUPPORTED_EXTENSIONS:
                size = filepath.stat().st_size
                if 10 < size < 1_000_000:
                    if self.train_from_file(filepath):
                        count += 1

        self.training_sessions += 1
        return count

    def train_from_web_data(self, code_data, language="python", source="web"):
        for code in code_data:
            if code and len(code.strip()) > 20:
                self.train(code, language)
                self.knowledge.add_snippet(language, code, source=source)

    def self_learn(self, user_input, user_accepted):
        if not user_input or not user_accepted:
            return

        tokens = self.tokenizer.tokenize(user_input)
        accepted_tokens = self.tokenizer.tokenize(user_accepted)

        if len(tokens) >= self.ngram_size - 1:
            context = tuple(tokens[-(self.ngram_size - 1):])
            for token in accepted_tokens:
                self.ngrams[context][token] += 3

        if tokens and accepted_tokens:
            self.transitions[tokens[-1]][accepted_tokens[0]] += 3

        combined = user_input.split("\n")[-1].strip() + " " + user_accepted
        words = combined.split()
        if len(words) >= 2:
            prefix = words[0]
            completion = " ".join(words[1:])
            self.line_patterns[prefix][completion] += 2

        self.accuracy_log.append({
            "timestamp": time.time(),
            "accepted": True,
        })

    def get_accuracy(self, last_n=100):
        if not self.accuracy_log:
            return 0.0

        recent = self.accuracy_log[-last_n:]
        accepted = sum(1 for log in recent if log.get("accepted"))
        return accepted / len(recent) * 100

    def get_model_stats(self):
        return {
            "ngram_entries": len(self.ngrams),
            "transition_entries": len(self.transitions),
            "line_patterns": len(self.line_patterns),
            "block_patterns": len(self.block_patterns),
            "vocab_size": self.tokenizer.get_vocab_size(),
            "total_tokens_trained": self.total_tokens_trained,
            "training_sessions": self.training_sessions,
            "accuracy": self.get_accuracy(),
            "last_trained": self.last_trained,
        }

    def save_model(self):
        if not self.model_path:
            return

        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "ngram_size": self.ngram_size,
            "ngrams": {str(k): dict(v) for k, v in self.ngrams.items()},
            "transitions": {k: dict(v) for k, v in self.transitions.items()},
            "line_patterns": {k: dict(v) for k, v in self.line_patterns.items()},
            "block_patterns": {k: dict(v) for k, v in self.block_patterns.items()},
            "document_freq": dict(self.document_freq),
            "total_documents": self.total_documents,
            "total_tokens_trained": self.total_tokens_trained,
            "training_sessions": self.training_sessions,
            "last_trained": self.last_trained,
            "accuracy_log": self.accuracy_log[-500:],
            "tokenizer_state": self.tokenizer.export_state(),
        }

        try:
            with open(self.model_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
        except Exception:
            pass

    def load_model(self):
        if not self.model_path or not self.model_path.exists():
            return

        try:
            with open(self.model_path, "r", encoding="utf-8") as f:
                state = json.load(f)

            self.ngram_size = state.get("ngram_size", self.ngram_size)

            for key_str, counts in state.get("ngrams", {}).items():
                key = tuple(eval(key_str)) if key_str.startswith("(") else tuple(key_str.split(","))
                self.ngrams[key] = Counter(counts)

            for key, counts in state.get("transitions", {}).items():
                self.transitions[key] = Counter(counts)

            for key, counts in state.get("line_patterns", {}).items():
                self.line_patterns[key] = Counter(counts)

            for key, counts in state.get("block_patterns", {}).items():
                self.block_patterns[key] = Counter(counts)

            self.document_freq = Counter(state.get("document_freq", {}))
            self.total_documents = state.get("total_documents", 0)
            self.total_tokens_trained = state.get("total_tokens_trained", 0)
            self.training_sessions = state.get("training_sessions", 0)
            self.last_trained = state.get("last_trained", 0)
            self.accuracy_log = state.get("accuracy_log", [])

            self.tokenizer.import_state(state.get("tokenizer_state"))

        except Exception:
            pass

    def reset_model(self):
        self.ngrams = defaultdict(Counter)
        self.transitions = defaultdict(Counter)
        self.line_patterns = defaultdict(Counter)
        self.block_patterns = defaultdict(Counter)
        self.document_freq = Counter()
        self.total_documents = 0
        self.total_tokens_trained = 0
        self.training_sessions = 0
        self.accuracy_log = []
