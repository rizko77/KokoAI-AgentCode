import re
from collections import Counter


class CodeTokenizer:

    KEYWORDS = {
        "python": {
            "def", "class", "if", "elif", "else", "for", "while", "try",
            "except", "finally", "with", "as", "import", "from", "return",
            "yield", "lambda", "pass", "break", "continue", "raise",
            "global", "nonlocal", "assert", "del", "True", "False", "None",
            "and", "or", "not", "in", "is", "async", "await", "self",
            "print", "len", "range", "list", "dict", "set", "tuple",
            "str", "int", "float", "bool", "type", "isinstance",
            "super", "property", "staticmethod", "classmethod",
            "__init__", "__str__", "__repr__", "__name__", "__main__",
        },
        "javascript": {
            "function", "var", "let", "const", "if", "else", "for", "while",
            "do", "switch", "case", "break", "continue", "return", "try",
            "catch", "finally", "throw", "new", "this", "class", "extends",
            "import", "export", "default", "from", "async", "await",
            "true", "false", "null", "undefined", "typeof", "instanceof",
            "console", "log", "document", "window", "require", "module",
            "Promise", "Array", "Object", "String", "Number", "Boolean",
            "map", "filter", "reduce", "forEach", "find", "includes",
            "addEventListener", "querySelector", "getElementById",
        },
        "html": {
            "html", "head", "body", "div", "span", "p", "a", "img",
            "ul", "ol", "li", "table", "tr", "td", "th", "form",
            "input", "button", "select", "option", "textarea",
            "h1", "h2", "h3", "h4", "h5", "h6", "header", "footer",
            "nav", "main", "section", "article", "aside", "script",
            "style", "link", "meta", "title", "class", "id", "href",
            "src", "alt", "type", "value", "name", "placeholder",
        },
        "css": {
            "color", "background", "margin", "padding", "border",
            "font", "display", "position", "width", "height",
            "flex", "grid", "align", "justify", "text", "transform",
            "transition", "animation", "opacity", "overflow",
            "hover", "focus", "active", "before", "after",
            "important", "none", "auto", "inherit", "initial",
            "px", "em", "rem", "vh", "vw", "rgb", "rgba", "hsl",
        },
    }

    TOKEN_PATTERNS = [
        ("STRING_DOUBLE", r'"(?:[^"\\]|\\.)*"'),
        ("STRING_SINGLE", r"'(?:[^'\\]|\\.)*'"),
        ("STRING_TEMPLATE", r'`(?:[^`\\]|\\.)*`'),
        ("COMMENT_MULTI", r'/\*[\s\S]*?\*/'),
        ("COMMENT_SINGLE", r'//[^\n]*|#[^\n]*'),
        ("NUMBER", r'\b\d+\.?\d*\b'),
        ("OPERATOR", r'[+\-*/=<>!&|^~%]+|\.{3}'),
        ("BRACKET", r'[(){}\[\]]'),
        ("PUNCTUATION", r'[,;:.]'),
        ("IDENTIFIER", r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
        ("WHITESPACE", r'\s+'),
        ("NEWLINE", r'\n'),
    ]

    def __init__(self):
        self.pattern = re.compile(
            '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_PATTERNS)
        )
        self.vocab = Counter()
        self.token_to_id = {"<PAD>": 0, "<UNK>": 1, "<START>": 2, "<END>": 3}
        self.id_to_token = {0: "<PAD>", 1: "<UNK>", 2: "<START>", 3: "<END>"}
        self.next_id = 4

    def tokenize(self, code, language="python"):
        tokens = []
        for match in self.pattern.finditer(code):
            token_type = match.lastgroup
            token_value = match.group()

            if token_type == "WHITESPACE":
                if token_value.startswith(("\t", "    ")):
                    tokens.append("<INDENT>")
                continue
            elif token_type == "NEWLINE":
                tokens.append("<NEWLINE>")
                continue

            if token_type in ("STRING_DOUBLE", "STRING_SINGLE", "STRING_TEMPLATE"):
                tokens.append("<STRING>")
                continue

            if token_type in ("COMMENT_SINGLE", "COMMENT_MULTI"):
                tokens.append("<COMMENT>")
                continue

            tokens.append(token_value)

        return tokens

    def tokenize_with_context(self, code, language="python"):
        tokens = []
        keywords = self.KEYWORDS.get(language, set())

        for match in self.pattern.finditer(code):
            token_type = match.lastgroup
            token_value = match.group()

            if token_type == "WHITESPACE" or token_type == "NEWLINE":
                continue

            if token_type == "IDENTIFIER" and token_value in keywords:
                token_type = "KEYWORD"

            tokens.append((token_value, token_type))

        return tokens

    def build_vocab(self, token_list):
        self.vocab.update(token_list)
        for token in token_list:
            if token not in self.token_to_id:
                self.token_to_id[token] = self.next_id
                self.id_to_token[self.next_id] = token
                self.next_id += 1

    def encode(self, tokens):
        return [self.token_to_id.get(t, 1) for t in tokens]

    def decode(self, ids):
        return [self.id_to_token.get(i, "<UNK>") for i in ids]

    def get_vocab_size(self):
        return len(self.token_to_id)

    def get_common_tokens(self, n=50):
        return self.vocab.most_common(n)

    def detect_language(self, code):
        scores = {}
        tokens = set(re.findall(r'\b[a-zA-Z_]\w*\b', code))

        for lang, keywords in self.KEYWORDS.items():
            score = len(tokens & keywords)
            scores[lang] = score

        if "def " in code or "import " in code or "self." in code:
            scores["python"] = scores.get("python", 0) + 5
        if "function " in code or "=>" in code or "var " in code or "const " in code:
            scores["javascript"] = scores.get("javascript", 0) + 5
        if "<html" in code.lower() or "<div" in code.lower():
            scores["html"] = scores.get("html", 0) + 5
        if "{" in code and ":" in code and ";" in code and "px" in code:
            scores["css"] = scores.get("css", 0) + 5

        if not scores:
            return "python"

        return max(scores, key=scores.get)

    def export_state(self):
        return {
            "vocab": dict(self.vocab),
            "token_to_id": self.token_to_id,
            "next_id": self.next_id,
        }

    def import_state(self, state):
        if not state:
            return
        self.vocab = Counter(state.get("vocab", {}))
        self.token_to_id = state.get("token_to_id", self.token_to_id)
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}
        self.next_id = state.get("next_id", self.next_id)
