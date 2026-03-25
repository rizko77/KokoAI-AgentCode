import os
import shutil
from pathlib import Path
from config.settings import WORKSPACE_DIR, SUPPORTED_EXTENSIONS


class CodeGenerator:

    def __init__(self, workspace=None):
        self.workspace = Path(workspace) if workspace else WORKSPACE_DIR
        self.workspace.mkdir(parents=True, exist_ok=True)

    def create_file(self, filename, content="", language=None):
        filepath = self._resolve_path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filepath.exists():
            return {"success": False, "error": f"File sudah ada: {filepath}"}

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(filepath), "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, filename):
        filepath = self._resolve_path(filename)

        if not filepath.exists():
            return {"success": False, "error": f"File tidak ditemukan: {filepath}"}

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")
            ext = filepath.suffix.lower()
            language = SUPPORTED_EXTENSIONS.get(ext, "text")

            return {
                "success": True,
                "path": str(filepath),
                "content": content,
                "lines": len(lines),
                "size": len(content),
                "language": language,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_file(self, filename, content=None, insert_at=None, insert_content=None,
                    replace_old=None, replace_new=None):
        filepath = self._resolve_path(filename)

        if not filepath.exists():
            return {"success": False, "error": f"File tidak ditemukan: {filepath}"}

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                original = f.read()

            if content is not None:
                new_content = content
            elif replace_old is not None and replace_new is not None:
                if replace_old not in original:
                    return {"success": False, "error": "Teks yang dicari tidak ditemukan"}
                new_content = original.replace(replace_old, replace_new)
            elif insert_at is not None and insert_content is not None:
                lines = original.split("\n")
                line_idx = max(0, min(insert_at - 1, len(lines)))
                lines.insert(line_idx, insert_content)
                new_content = "\n".join(lines)
            else:
                return {"success": False, "error": "Parameter update tidak valid"}

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {
                "success": True,
                "path": str(filepath),
                "original_size": len(original),
                "new_size": len(new_content),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, filename):
        filepath = self._resolve_path(filename)

        if not filepath.exists():
            return {"success": False, "error": f"File tidak ditemukan: {filepath}"}

        try:
            if filepath.is_dir():
                shutil.rmtree(filepath)
                return {"success": True, "path": str(filepath), "type": "directory"}
            else:
                filepath.unlink()
                return {"success": True, "path": str(filepath), "type": "file"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_project(self, project_name, project_type="python", structure=None):
        project_dir = self.workspace / project_name
        if project_dir.exists():
            return {"success": False, "error": f"Project sudah ada: {project_dir}"}

        project_dir.mkdir(parents=True, exist_ok=True)

        if structure:
            files_created = self._create_from_structure(project_dir, structure)
        else:
            files_created = self._create_default_project(project_dir, project_type, project_name)

        return {
            "success": True,
            "path": str(project_dir),
            "files_created": files_created,
            "type": project_type,
        }

    def list_workspace(self, subpath=""):
        target = self.workspace / subpath if subpath else self.workspace
        if not target.exists():
            return {"success": False, "error": "Path tidak ditemukan"}

        items = []
        for item in sorted(target.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", "venv"):
                continue
            info = {
                "name": item.name,
                "is_dir": item.is_dir(),
                "path": str(item.relative_to(self.workspace)),
            }
            if item.is_file():
                info["size"] = item.stat().st_size
                info["language"] = SUPPORTED_EXTENSIONS.get(item.suffix.lower(), "unknown")
            items.append(info)

        return {"success": True, "path": str(target), "items": items}

    def rename_file(self, old_name, new_name):
        old_path = self._resolve_path(old_name)
        new_path = self._resolve_path(new_name)

        if not old_path.exists():
            return {"success": False, "error": f"File tidak ditemukan: {old_path}"}
        if new_path.exists():
            return {"success": False, "error": f"Nama baru sudah ada: {new_path}"}

        try:
            old_path.rename(new_path)
            return {"success": True, "old": str(old_path), "new": str(new_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _resolve_path(self, filename):
        path = Path(filename)
        if path.is_absolute():
            return path
        return self.workspace / filename

    def _create_from_structure(self, base_dir, structure):
        created = []
        for item in structure:
            if isinstance(item, dict):
                name = item.get("name", "")
                content = item.get("content", "")
                filepath = base_dir / name
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                created.append(name)
            elif isinstance(item, str):
                if item.endswith("/"):
                    (base_dir / item).mkdir(parents=True, exist_ok=True)
                else:
                    filepath = base_dir / item
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.touch()
                    created.append(item)
        return created

    def _create_default_project(self, project_dir, project_type, name):
        templates = {
            "python": [
                {"name": "main.py", "content": f'def main():\n    print("Selamat datang di {name}!")\n\n\nif __name__ == "__main__":\n    main()\n'},
                {"name": "requirements.txt", "content": ""},
                {"name": "README.md", "content": f"# {name}\n\nDeskripsi project.\n"},
                {"name": ".gitignore", "content": "__pycache__/\n*.pyc\nvenv/\n.env\n"},
            ],
            "web": [
                {"name": "index.html", "content": f'<!DOCTYPE html>\n<html lang="id">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{name}</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <h1>{name}</h1>\n    <script src="script.js"></script>\n</body>\n</html>\n'},
                {"name": "style.css", "content": "* {\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}\n\nbody {\n    font-family: sans-serif;\n}\n"},
                {"name": "script.js", "content": f'console.log("{name} loaded");\n'},
            ],
            "flask": [
                {"name": "app.py", "content": f'from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef index():\n    return "{name} is running!"\n\nif __name__ == "__main__":\n    app.run(debug=True)\n'},
                {"name": "requirements.txt", "content": "flask\n"},
                {"name": "templates/index.html", "content": f"<h1>{name}</h1>\n"},
            ],
            "node": [
                {"name": "index.js", "content": f'console.log("{name} started");\n'},
                {"name": "package.json", "content": f'{{\n  "name": "{name.lower()}",\n  "version": "1.0.0",\n  "main": "index.js"\n}}\n'},
            ],
        }

        structure = templates.get(project_type, templates["python"])
        return self._create_from_structure(project_dir, structure)
