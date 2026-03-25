import time
import json
import threading
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta


class TrainingScheduler:

    TRAINING_TOPICS = {
        "python": [
            "python data structures", "python algorithms", "python design patterns",
            "python web scraping", "python file handling", "python async programming",
            "python decorators", "python generators", "python context managers",
            "python error handling best practices", "python OOP patterns",
            "python functional programming", "python regex patterns",
            "python sorting algorithms", "python graph algorithms",
            "python REST API", "python database operations",
            "python testing patterns", "python logging best practices",
        ],
        "javascript": [
            "javascript async await", "javascript promises", "javascript closures",
            "javascript array methods", "javascript DOM manipulation",
            "javascript fetch API", "javascript event handling",
            "javascript ES6 features", "javascript design patterns",
            "javascript error handling", "javascript modules",
        ],
        "html": [
            "html5 semantic elements", "html form validation",
            "html accessibility best practices", "html responsive design",
        ],
        "css": [
            "css flexbox layout", "css grid layout", "css animations",
            "css responsive design", "css variables custom properties",
        ],
    }

    def __init__(self, engine, interval_minutes=60, log_path=None):
        self.engine = engine
        self.interval = interval_minutes * 60
        self.log_path = Path(log_path) if log_path else None
        self.is_running = False
        self.thread = None
        self.training_log = []
        self.last_training_time = 0
        self.topics_trained = set()
        self._load_log()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self._save_log()

    def _scheduler_loop(self):
        while self.is_running:
            time.sleep(self.interval)
            if not self.is_running:
                break
            self._run_training_session()

    def _run_training_session(self):
        session = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "snippets_learned": 0,
            "files_trained": 0,
            "sources": [],
            "errors": [],
        }

        try:
            from config.settings import WORKSPACE_DIR
            file_count = self.engine.train_directory(WORKSPACE_DIR)
            session["files_trained"] = file_count
        except Exception as e:
            session["errors"].append(f"Workspace training: {e}")

        try:
            topic = self._pick_topic()
            if topic:
                snippets = self._fetch_and_train(topic)
                session["snippets_learned"] = snippets
                session["sources"].append(f"internet:{topic}")
                self.topics_trained.add(topic)
        except Exception as e:
            session["errors"].append(f"Internet training: {e}")

        try:
            self.engine.brain.save_model()
            self.engine.knowledge.save()
        except Exception:
            pass

        self.last_training_time = time.time()
        self.training_log.append(session)
        if len(self.training_log) > 500:
            self.training_log = self.training_log[-500:]
        self._save_log()

        return session

    def _pick_topic(self):
        all_topics = []
        for lang, topics in self.TRAINING_TOPICS.items():
            for topic in topics:
                if topic not in self.topics_trained:
                    all_topics.append(topic)

        if not all_topics:
            self.topics_trained.clear()
            for lang, topics in self.TRAINING_TOPICS.items():
                all_topics.extend(topics)

        if all_topics:
            return random.choice(all_topics)
        return None

    def _fetch_and_train(self, topic):
        total = 0

        try:
            from tool.multi_source import collect_code_snippets
            snippets = collect_code_snippets(topic, max_total=10)
            if snippets:
                language = "python"
                for lang in self.TRAINING_TOPICS:
                    if topic in self.TRAINING_TOPICS[lang]:
                        language = lang
                        break
                self.engine.brain.train_from_web_data(snippets, language, source=f"auto:{topic}")
                total = len(snippets)
        except Exception:
            pass

        return total

    def force_training(self):
        return self._run_training_session()

    def get_stats(self):
        total_snippets = sum(s.get("snippets_learned", 0) for s in self.training_log)
        total_sessions = len(self.training_log)
        return {
            "total_sessions": total_sessions,
            "total_snippets_learned": total_snippets,
            "topics_covered": len(self.topics_trained),
            "last_training": self.last_training_time,
            "is_running": self.is_running,
            "interval_minutes": self.interval // 60,
        }

    def get_recent_logs(self, n=10):
        return self.training_log[-n:]

    def _save_log(self):
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "training_log": self.training_log[-200:],
            "topics_trained": list(self.topics_trained),
            "last_training_time": self.last_training_time,
        }
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def _load_log(self):
        if not self.log_path or not self.log_path.exists():
            return
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.training_log = data.get("training_log", [])
            self.topics_trained = set(data.get("topics_trained", []))
            self.last_training_time = data.get("last_training_time", 0)
        except Exception:
            pass
