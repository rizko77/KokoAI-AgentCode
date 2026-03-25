from pathlib import Path


def read_file(filepath, encoding="utf-8"):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding=encoding, errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def write_file(filepath, content, encoding="utf-8"):
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def append_file(filepath, content, encoding="utf-8"):
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "a", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def read_lines(filepath, start=0, end=None, encoding="utf-8"):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return []

        with open(filepath, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()

        return lines[start:end]
    except Exception:
        return []


def count_lines(filepath, encoding="utf-8"):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return 0

        with open(filepath, "r", encoding=encoding, errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def search_in_file(filepath, query, case_sensitive=False):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return []

        results = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if case_sensitive:
                    if query in line:
                        results.append((i, line.rstrip()))
                else:
                    if query.lower() in line.lower():
                        results.append((i, line.rstrip()))

        return results
    except Exception:
        return []


def get_file_context(filepath, line_number, context_lines=5):
    lines = read_lines(filepath)
    if not lines:
        return {}

    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)

    context = {}
    for i in range(start, end):
        context[i + 1] = lines[i].rstrip()

    return context
