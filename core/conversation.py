import json
import time
from pathlib import Path
from collections import deque


class ConversationMemory:

    def __init__(self, max_turns=100, save_path=None):
        self.turns = deque(maxlen=max_turns)
        self.context_stack = []
        self.active_file = None
        self.active_language = "python"
        self.user_preferences = {}
        self.save_path = Path(save_path) if save_path else None
        self._load()

    def add_turn(self, role, content, metadata=None):
        turn = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self.turns.append(turn)
        return turn

    def add_user(self, content, intent=None, entities=None):
        meta = {}
        if intent:
            meta["intent"] = intent
        if entities:
            meta["entities"] = entities
        return self.add_turn("user", content, meta)

    def add_assistant(self, content, mode=None, action=None):
        meta = {}
        if mode:
            meta["mode"] = mode
        if action:
            meta["action"] = action
        return self.add_turn("assistant", content, meta)

    def get_recent(self, n=10):
        turns_list = list(self.turns)
        return turns_list[-n:]

    def get_context_summary(self):
        recent = self.get_recent(5)
        if not recent:
            return ""

        parts = []
        for turn in recent:
            role = turn["role"]
            content = turn["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            parts.append(f"[{role}] {content}")

        return "\n".join(parts)

    def get_last_intent(self):
        for turn in reversed(list(self.turns)):
            if turn["role"] == "user":
                return turn.get("metadata", {}).get("intent")
        return None

    def get_last_file(self):
        for turn in reversed(list(self.turns)):
            entities = turn.get("metadata", {}).get("entities", {})
            if "filepath" in entities:
                files = entities["filepath"]
                if files:
                    return files[0]
        return self.active_file

    def set_active_file(self, filepath):
        self.active_file = filepath

    def set_active_language(self, language):
        self.active_language = language

    def push_context(self, context_type, data):
        self.context_stack.append({
            "type": context_type,
            "data": data,
            "timestamp": time.time(),
        })
        if len(self.context_stack) > 20:
            self.context_stack = self.context_stack[-20:]

    def pop_context(self):
        if self.context_stack:
            return self.context_stack.pop()
        return None

    def get_current_context(self):
        return {
            "active_file": self.active_file,
            "active_language": self.active_language,
            "turn_count": len(self.turns),
            "last_intent": self.get_last_intent(),
            "context_depth": len(self.context_stack),
        }

    def clear(self):
        self.turns.clear()
        self.context_stack = []

    def save(self):
        if not self.save_path:
            return
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "turns": list(self.turns)[-50:],
            "active_file": self.active_file,
            "active_language": self.active_language,
            "user_preferences": self.user_preferences,
        }
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def _load(self):
        if not self.save_path or not self.save_path.exists():
            return
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for turn in data.get("turns", []):
                self.turns.append(turn)
            self.active_file = data.get("active_file")
            self.active_language = data.get("active_language", "python")
            self.user_preferences = data.get("user_preferences", {})
        except Exception:
            pass
