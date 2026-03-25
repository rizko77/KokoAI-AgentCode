import os
from pathlib import Path
from config.settings import SUPPORTED_EXTENSIONS


def list_files(directory, recursive=False, extensions=None):
    directory = Path(directory)
    if not directory.exists():
        return []

    files = []
    pattern = "**/*" if recursive else "*"

    for item in directory.glob(pattern):
        if item.is_file():
            if extensions is None or item.suffix.lower() in extensions:
                files.append(str(item))

    return sorted(files)


def list_code_files(directory, recursive=True):
    return list_files(directory, recursive, set(SUPPORTED_EXTENSIONS.keys()))


def get_file_info(filepath):
    filepath = Path(filepath)
    if not filepath.exists():
        return {"error": "File tidak ditemukan"}

    stat = filepath.stat()

    return {
        "name": filepath.name,
        "extension": filepath.suffix,
        "size_bytes": stat.st_size,
        "size_readable": _format_size(stat.st_size),
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "is_code": filepath.suffix.lower() in SUPPORTED_EXTENSIONS,
        "language": SUPPORTED_EXTENSIONS.get(filepath.suffix.lower(), "unknown"),
        "parent": str(filepath.parent),
        "absolute": str(filepath.absolute()),
    }


def search_files(directory, pattern, recursive=True):
    directory = Path(directory)
    if not directory.exists():
        return []

    glob_pattern = f"**/{pattern}" if recursive else pattern
    return sorted([str(p) for p in directory.glob(glob_pattern) if p.is_file()])


def get_directory_tree(directory, max_depth=3, prefix=""):
    directory = Path(directory)
    if not directory.exists() or max_depth < 0:
        return ""

    lines = []
    items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "

        if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", "venv", ".git"):
            continue

        if item.is_dir():
            lines.append(f"{prefix}{connector}📁 {item.name}/")
            extension = "    " if is_last else "│   "
            sub_tree = get_directory_tree(item, max_depth - 1, prefix + extension)
            if sub_tree:
                lines.append(sub_tree)
        else:
            size = _format_size(item.stat().st_size)
            lines.append(f"{prefix}{connector}📄 {item.name} ({size})")

    return "\n".join(lines)


def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"
