import time
from collections import defaultdict


class ThinkingMode:

    MODES = {
        "thinking": {
            "name": "🧠 Thinking",
            "description": "Deep analysis & architecture planning",
            "max_suggestions": 10,
            "context_depth": 20,
            "ngram_lookback": 5,
            "use_web_search": True,
            "use_knowledge": True,
            "multi_step": True,
            "explain": True,
            "code_analysis": True,
            "timeout": 60,
        },
        "reasoning": {
            "name": "💡 Reasoning",
            "description": "Logical analysis & debugging",
            "max_suggestions": 7,
            "context_depth": 15,
            "ngram_lookback": 4,
            "use_web_search": False,
            "use_knowledge": True,
            "multi_step": True,
            "explain": True,
            "code_analysis": True,
            "timeout": 30,
        },
        "medium": {
            "name": "⚡ Medium",
            "description": "Balanced speed & quality",
            "max_suggestions": 5,
            "context_depth": 10,
            "ngram_lookback": 3,
            "use_web_search": False,
            "use_knowledge": True,
            "multi_step": False,
            "explain": False,
            "code_analysis": False,
            "timeout": 15,
        },
        "fast": {
            "name": "🚀 Fast",
            "description": "Quick suggestions & answers",
            "max_suggestions": 3,
            "context_depth": 5,
            "ngram_lookback": 2,
            "use_web_search": False,
            "use_knowledge": False,
            "multi_step": False,
            "explain": False,
            "code_analysis": False,
            "timeout": 5,
        },
    }

    def __init__(self):
        self.current_mode = "thinking"
        self.mode_history = []
        self.mode_stats = defaultdict(lambda: {"uses": 0, "total_time": 0.0})

    def set_mode(self, mode_name):
        mode_name = mode_name.lower().strip()
        if mode_name not in self.MODES:
            return None

        self.current_mode = mode_name
        self.mode_history.append({
            "mode": mode_name,
            "timestamp": time.time(),
        })

        return self.get_mode_config()

    def get_mode_config(self):
        return self.MODES.get(self.current_mode, self.MODES["medium"]).copy()

    def get_mode_name(self):
        config = self.get_mode_config()
        return config["name"]

    def auto_select_mode(self, nlu_result):
        # Force "thinking" mode as requested by user
        suggestion = "thinking" 
        self.set_mode(suggestion)
        return suggestion

    def process_with_mode(self, engine, user_input, nlu_result):
        config = self.get_mode_config()
        start_time = time.time()

        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})

        response = {
            "mode": self.current_mode,
            "mode_name": config["name"],
            "intent": intent,
            "steps": [],
            "result": None,
            "suggestions": [],
            "explanation": "",
            "sources": [],
            "time_elapsed": 0,
        }

        if config["code_analysis"]:
            step = self._step_analyze_context(engine, user_input, config)
            response["steps"].append(step)

        if intent in ("suggest_code", "generate_code", "create_file", "unknown"):
            step = self._step_get_suggestions(engine, user_input, config)
            response["steps"].append(step)
            response["suggestions"] = step.get("data", [])

        if config["use_knowledge"] and intent in ("explain_code", "search_code",
                                                    "debug_code", "generate_code"):
            step = self._step_search_knowledge(engine, user_input, config)
            response["steps"].append(step)

        if config["use_web_search"] and intent in ("search_code", "explain_code",
                                                    "generate_code"):
            step = self._step_web_search(engine, user_input, config)
            response["steps"].append(step)
            response["sources"] = step.get("data", [])

        if config["multi_step"] and intent in ("debug_code", "explain_code",
                                                "create_project"):
            step = self._step_multi_reasoning(engine, user_input, nlu_result, config)
            response["steps"].append(step)

        if config["explain"]:
            explanation = self._generate_explanation(response, nlu_result)
            response["explanation"] = explanation

        response["result"] = self._build_result(response, nlu_result)

        elapsed = time.time() - start_time
        response["time_elapsed"] = round(elapsed, 3)

        self.mode_stats[self.current_mode]["uses"] += 1
        self.mode_stats[self.current_mode]["total_time"] += elapsed

        return response

    def _step_analyze_context(self, engine, user_input, config):
        depth = config["context_depth"]
        lines = user_input.split("\n")

        context_lines = lines[-depth:] if len(lines) > depth else lines

        structures = []
        for line in context_lines:
            stripped = line.strip()
            if stripped.startswith("def "):
                structures.append(("function", stripped))
            elif stripped.startswith("class "):
                structures.append(("class", stripped))
            elif stripped.startswith("for ") or stripped.startswith("while "):
                structures.append(("loop", stripped))
            elif stripped.startswith("if "):
                structures.append(("condition", stripped))
            elif stripped.startswith("import ") or stripped.startswith("from "):
                structures.append(("import", stripped))

        return {
            "name": "Context Analysis",
            "status": "done",
            "data": {
                "total_lines": len(lines),
                "context_lines": len(context_lines),
                "structures": structures,
                "last_line": lines[-1] if lines else "",
            }
        }

    def _step_get_suggestions(self, engine, user_input, config):
        max_sugg = config["max_suggestions"]

        try:
            suggestions = engine.get_suggestions(user_input, max_suggestions=max_sugg)
            line_suggestions = engine.get_line_suggestions(user_input)

            combined = []
            for text, score in suggestions:
                combined.append({"type": "token", "text": text, "score": score})
            for text, score in line_suggestions:
                combined.append({"type": "line", "text": text, "score": score})

            return {
                "name": "Code Suggestions",
                "status": "done",
                "data": combined,
            }
        except Exception as e:
            return {
                "name": "Code Suggestions",
                "status": "error",
                "data": [],
                "error": str(e),
            }

    def _step_search_knowledge(self, engine, user_input, config):
        try:
            results = engine.search_knowledge(user_input)
            return {
                "name": "Knowledge Search",
                "status": "done",
                "data": results[:5],
            }
        except Exception as e:
            return {
                "name": "Knowledge Search",
                "status": "error",
                "data": [],
                "error": str(e),
            }

    def _step_web_search(self, engine, user_input, config):
        try:
            from tool.internet_search import search_code
            results = search_code(user_input)
            if results and "error" not in results[0]:
                return {
                    "name": "Web Search",
                    "status": "done",
                    "data": results[:5],
                }
            return {
                "name": "Web Search",
                "status": "no_results",
                "data": [],
            }
        except Exception as e:
            return {
                "name": "Web Search",
                "status": "error",
                "data": [],
                "error": str(e),
            }

    def _step_multi_reasoning(self, engine, user_input, nlu_result, config):
        intent = nlu_result["intent"]
        steps = []

        if intent == "debug_code":
            steps = [
                "1. Identifikasi error pattern dari input",
                "2. Cek syntax dan structure",
                "3. Cari common mistakes berdasarkan pattern",
                "4. Sarankan fix berdasarkan knowledge base",
                "5. Verifikasi logic flow",
            ]
        elif intent == "explain_code":
            steps = [
                "1. Parse struktur kode (fungsi, class, loop, dll)",
                "2. Identifikasi tujuan utama kode",
                "3. Jelaskan setiap bagian penting",
                "4. Berikan contoh penggunaan",
            ]
        elif intent == "create_project":
            steps = [
                "1. Analisis requirement dari deskripsi",
                "2. Tentukan struktur project",
                "3. Identifikasi file-file yang perlu dibuat",
                "4. Pilih library/framework yang sesuai",
                "5. Generate kode dasar",
            ]

        return {
            "name": "Multi-step Reasoning",
            "status": "done",
            "data": steps,
        }

    def _generate_explanation(self, response, nlu_result):
        intent = nlu_result["intent"]
        steps = response.get("steps", [])

        parts = [f"[{self.get_mode_name()}]"]
        parts.append(f"Intent terdeteksi: {intent}")

        if steps:
            parts.append(f"Langkah pemrosesan: {len(steps)}")
            for step in steps:
                status_icon = "✅" if step["status"] == "done" else "❌"
                parts.append(f"  {status_icon} {step['name']}")

        return "\n".join(parts)

    def _build_result(self, response, nlu_result):
        intent = nlu_result["intent"]

        all_data = {}
        for step in response["steps"]:
            all_data[step["name"]] = step.get("data", {})

        return {
            "intent": intent,
            "data": all_data,
            "has_suggestions": len(response.get("suggestions", [])) > 0,
            "has_sources": len(response.get("sources", [])) > 0,
        }

    def get_stats(self):
        stats = {}
        for mode, data in self.mode_stats.items():
            avg_time = data["total_time"] / max(data["uses"], 1)
            stats[mode] = {
                "uses": data["uses"],
                "total_time": round(data["total_time"], 2),
                "avg_time": round(avg_time, 3),
            }
        return stats

    def get_all_modes(self):
        result = []
        for mode_name, config in self.MODES.items():
            result.append({
                "name": mode_name,
                "display_name": config["name"],
                "description": config["description"],
                "is_current": mode_name == self.current_mode,
            })
        return result
