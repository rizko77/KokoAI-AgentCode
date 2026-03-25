"""
KokoAI 1.0 - Code Templates
Template kode untuk berbagai bahasa dan pattern umum.
Digunakan sebagai basis knowledge awal sebelum model di-train.
"""


# === Python Templates ===
PYTHON_TEMPLATES = {
    "class_basic": '''class {name}:
    """Deskripsi {name}."""

    def __init__(self):
        pass

    def __str__(self):
        return f"{name}()"
''',

    "class_init": '''class {name}:
    """Deskripsi {name}."""

    def __init__(self, {params}):
        self.{first_param} = {first_param}
''',

    "function": '''def {name}({params}):
    """
    Deskripsi fungsi {name}.
    
    Args:
        {params}: Parameter
        
    Returns:
        Hasil
    """
    pass
''',

    "for_loop": '''for {var} in {iterable}:
    {body}
''',

    "for_range": '''for i in range({n}):
    {body}
''',

    "for_enumerate": '''for i, {var} in enumerate({iterable}):
    {body}
''',

    "if_else": '''if {condition}:
    {true_body}
else:
    {false_body}
''',

    "try_except": '''try:
    {body}
except {exception} as e:
    print(f"Error: {{e}}")
''',

    "with_open": '''with open("{filepath}", "{mode}") as f:
    {body}
''',

    "list_comp": '''[{expression} for {var} in {iterable} if {condition}]''',

    "dict_comp": '''{{{key}: {value} for {var} in {iterable}}}''',

    "lambda": '''lambda {params}: {expression}''',

    "main_block": '''def main():
    {body}


if __name__ == "__main__":
    main()
''',

    "import_common": '''import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict
''',

    "argparse": '''import argparse

parser = argparse.ArgumentParser(description="{description}")
parser.add_argument("{arg}", type=str, help="{help}")
args = parser.parse_args()
''',

    "requests_get": '''import requests

response = requests.get("{url}")
if response.ok:
    data = response.json()
    print(data)
else:
    print(f"Error: {{response.status_code}}")
''',

    "flask_app": '''from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({{"message": "Hello from KokoAI!"}})

@app.route("/api/{route}", methods=["GET"])
def api_{route}():
    return jsonify({{"data": []}})

if __name__ == "__main__":
    app.run(debug=True) 
''',

    "fastapi_app": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    value: float

@app.get("/")
async def root():
    return {{"message": "Hello from KokoAI!"}}

@app.post("/items/")
async def create_item(item: Item):
    return item
''',
}

# === JavaScript Templates ===
JAVASCRIPT_TEMPLATES = {
    "function": '''function {name}({params}) {{
    {body}
}}
''',

    "arrow_function": '''const {name} = ({params}) => {{
    {body}
}};
''',

    "class": '''class {name} {{
    constructor({params}) {{
        this.{first_param} = {first_param};
    }}

    {method}() {{
        {body}
    }}
}}
''',

    "async_function": '''async function {name}({params}) {{
    try {{
        const response = await fetch("{url}");
        const data = await response.json();
        return data;
    }} catch (error) {{
        console.error("Error:", error);
    }}
}}
''',

    "promise": '''const {name} = new Promise((resolve, reject) => {{
    {body}
}});
''',

    "array_methods": '''const result = {array}
    .filter(item => {condition})
    .map(item => {transform})
    .reduce((acc, item) => {reducer}, {initial});
''',

    "event_listener": '''document.querySelector("{selector}")
    .addEventListener("{event}", (e) => {{
        {body}
    }});
''',

    "fetch_api": '''fetch("{url}", {{
    method: "{method}",
    headers: {{
        "Content-Type": "application/json",
    }},
    body: JSON.stringify({data}),
}})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error(err));
''',

    "express_server": '''const express = require("express");
const app = express();
const PORT = 3000;

app.use(express.json());

app.get("/", (req, res) => {{
    res.json({{ message: "Hello from KokoAI!" }});
}});

app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});
''',
}

# === HTML Templates ===
HTML_TEMPLATES = {
    "boilerplate": '''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav>
            <h1>{title}</h1>
        </nav>
    </header>

    <main>
        {content}
    </main>

    <footer>
        <p>&copy; 2026 {author}</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>
''',

    "form": '''<form id="{id}" method="{method}" action="{action}">
    <div class="form-group">
        <label for="{field}">{label}</label>
        <input type="{type}" id="{field}" name="{field}" required>
    </div>
    <button type="submit">Submit</button>
</form>
''',

    "card": '''<div class="card">
    <img src="{image}" alt="{alt}" class="card-image">
    <div class="card-body">
        <h3 class="card-title">{title}</h3>
        <p class="card-text">{description}</p>
        <a href="{link}" class="card-link">Read More</a>
    </div>
</div>
''',
}

# === CSS Templates ===
CSS_TEMPLATES = {
    "reset": '''* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
}}
''',

    "flexbox_center": '''display: flex;
justify-content: center;
align-items: center;
''',

    "grid_layout": '''display: grid;
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
gap: 1rem;
''',

    "dark_theme": ''':root {{
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
}}
''',

    "responsive": '''@media (max-width: 768px) {{
    .container {{
        padding: 1rem;
    }}
    
    .grid {{
        grid-template-columns: 1fr;
    }}
}}
''',
}


def get_template(language, template_name, **kwargs):
    """
    Ambil template dan isi placeholder.
    
    Args:
        language: Bahasa pemrograman
        template_name: Nama template
        **kwargs: Nilai untuk placeholder
        
    Returns:
        String template yang sudah diisi
    """
    templates = {
        "python": PYTHON_TEMPLATES,
        "javascript": JAVASCRIPT_TEMPLATES,
        "html": HTML_TEMPLATES,
        "css": CSS_TEMPLATES,
    }
    
    lang_templates = templates.get(language, {})
    template = lang_templates.get(template_name, "")
    
    if template and kwargs:
        try:
            # Replace {placeholder} dengan nilai, 
            # tapi hanya yang ada di kwargs
            for key, value in kwargs.items():
                template = template.replace(f"{{{key}}}", str(value))
        except Exception:
            pass
    
    return template


def get_all_template_names(language=None):
    """Dapatkan semua nama template yang tersedia."""
    templates = {
        "python": PYTHON_TEMPLATES,
        "javascript": JAVASCRIPT_TEMPLATES,
        "html": HTML_TEMPLATES,
        "css": CSS_TEMPLATES,
    }
    
    if language:
        return list(templates.get(language, {}).keys())
    
    result = {}
    for lang, tmpl in templates.items():
        result[lang] = list(tmpl.keys())
    return result


def get_initial_training_data():
    """
    Dapatkan semua template sebagai training data awal.
    
    Returns:
        Dictionary {language: [code_strings]}
    """
    data = {}
    
    all_templates = {
        "python": PYTHON_TEMPLATES,
        "javascript": JAVASCRIPT_TEMPLATES,
        "html": HTML_TEMPLATES,
        "css": CSS_TEMPLATES,
    }
    
    for language, templates in all_templates.items():
        data[language] = list(templates.values())
    
    return data
