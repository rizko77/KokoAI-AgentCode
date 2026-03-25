from pathlib import Path
from config.settings import SUPPORTED_EXTENSIONS


def build_code_context(filepath, cursor_line=None, context_lines=10):
    filepath = Path(filepath)
    if not filepath.exists():
        return {}

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return {}

    total_lines = len(lines)

    ext = filepath.suffix.lower()
    language = SUPPORTED_EXTENSIONS.get(ext, "python")

    if cursor_line is None:
        cursor_line = total_lines

    start = max(0, cursor_line - context_lines - 1)
    end = min(total_lines, cursor_line + context_lines)

    context_before = "".join(lines[start:cursor_line - 1]) if cursor_line > 1 else ""
    current_line = lines[cursor_line - 1] if cursor_line <= total_lines else ""
    context_after = "".join(lines[cursor_line:end]) if cursor_line < total_lines else ""

    return {
        "filepath": str(filepath),
        "filename": filepath.name,
        "language": language,
        "total_lines": total_lines,
        "cursor_line": cursor_line,
        "context_before": context_before,
        "current_line": current_line.rstrip(),
        "context_after": context_after,
        "full_context": context_before + current_line,
    }


def build_project_context(directory, max_files=20):
    directory = Path(directory)
    if not directory.exists():
        return {}

    files = []
    languages = set()

    for filepath in directory.rglob("*"):
        if filepath.is_file():
            ext = filepath.suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                language = SUPPORTED_EXTENSIONS[ext]
                languages.add(language)

                files.append({
                    "path": str(filepath.relative_to(directory)),
                    "language": language,
                    "size": filepath.stat().st_size,
                })

                if len(files) >= max_files:
                    break

    framework = detect_framework(directory)

    return {
        "directory": str(directory),
        "files": files,
        "total_files": len(files),
        "languages": list(languages),
        "primary_language": max(languages, key=lambda l: sum(1 for f in files if f["language"] == l)) if languages else "python",
        "framework": framework,
    }


def detect_framework(directory):
    directory = Path(directory)

    checks = {
        "django": ["manage.py", "settings.py"],
        "flask": ["app.py"],
        "fastapi": ["main.py"],
        "react": ["package.json"],
        "vue": ["vue.config.js"],
        "next": ["next.config.js"],
        "laravel": ["artisan", "composer.json"],
    }

    for framework, indicators in checks.items():
        for indicator in indicators:
            if (directory / indicator).exists():
                if framework == "react":
                    pkg = directory / "package.json"
                    if pkg.exists():
                        try:
                            content = pkg.read_text()
                            if '"react"' in content:
                                return "react"
                            elif '"vue"' in content:
                                return "vue"
                            elif '"next"' in content:
                                return "next"
                        except Exception:
                            pass
                    continue
                return framework

    return "none"


def build_suggestion_prompt(context, suggestions):
    if not context or not suggestions:
        return ""

    lines = [
        f"File: {context.get('filename', 'unknown')}",
        f"Language: {context.get('language', 'unknown')}",
        f"Line: {context.get('cursor_line', '?')}",
        "",
        "Current:",
        f"  {context.get('current_line', '')}",
        "",
        "Suggestions:",
    ]

    for i, (text, score) in enumerate(suggestions, 1):
        bar_len = int(score * 20) if score <= 1 else int(min(score, 100) / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        lines.append(f"  [{i}] {text}")
        lines.append(f"      [{bar}] {score:.1%}")

    return "\n".join(lines)
