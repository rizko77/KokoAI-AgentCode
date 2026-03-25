"""
KokoAI - NLP Utilities
Wrapper untuk nlp-id, indoNLP, dan NLTK.
Dipanggil oleh nlu.py dan engine.py.
"""
# Fungsi-fungsi NLP utama sudah ada di core/nlu.py
# File ini hanya re-export agar modul lain bisa import dari core.nlp

from core.nlu import (
    lemmatize_text,
    get_stopwords,
    extract_keywords,
    normalize_verbs,
    VERB_ROOT_MAP,
)

__all__ = [
    "lemmatize_text",
    "get_stopwords",
    "extract_keywords",
    "normalize_verbs",
    "VERB_ROOT_MAP",
]
