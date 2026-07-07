"""Text post-processing for OpenWispr transcriptions.

Whisper's raw output needs help to read like typed text: it sometimes skips
punctuation, keeps filler sounds, and hallucinates YouTube-style credits on
silence. This module turns raw segments into clean, well-punctuated text and
optionally applies spoken punctuation commands ("запятая", "new line", ...).
"""

import re

# Whisper mirrors the style of the initial prompt, so a well-punctuated prompt
# in the target language is the single biggest lever for getting punctuation.
_PROMPTS = {
    "ru": ("Привет! Это аккуратная диктовка: текст с правильной пунктуацией — "
           "запятые, точки, тире, вопросительные и восклицательные знаки."),
    "uk": ("Привіт! Це акуратна диктовка: текст із правильною пунктуацією — "
           "коми, крапки, тире, знаки питання та оклику."),
    "en": ("Hello! This is a careful dictation: text with proper punctuation — "
           "commas, periods, dashes, question marks and exclamation points."),
    "de": ("Hallo! Dies ist ein sorgfältiges Diktat: Text mit korrekter "
           "Zeichensetzung — Kommas, Punkte, Fragezeichen."),
    "fr": ("Bonjour ! Ceci est une dictée soignée : un texte bien ponctué — "
           "virgules, points, points d'interrogation."),
    "es": ("¡Hola! Este es un dictado cuidadoso: texto con puntuación "
           "correcta — comas, puntos, signos de interrogación."),
    "it": ("Ciao! Questo è un dettato accurato: testo con punteggiatura "
           "corretta — virgole, punti, punti interrogativi."),
    "pl": ("Cześć! To staranne dyktando: tekst z poprawną interpunkcją — "
           "przecinki, kropki, znaki zapytania."),
}

# Classic Whisper hallucinations on silence/noise. A sentence containing any
# of these is dropped entirely.
_HALLUCINATIONS = (
    "субтитры делал", "субтитры сделал", "субтитры создавал",
    "субтитры подготовил", "субтитры подогнал", "редактор субтитров",
    "корректор а.", "продолжение следует", "спасибо за просмотр",
    "подписывайтесь на канал", "ставьте лайки", "динамическая реклама",
    "фильм снят", "игорь негода", "dimatorzok",
    "thanks for watching", "thank you for watching", "please subscribe",
    "like and subscribe", "see you in the next video", "subtitles by",
    "amara.org", "www.youtube.com",
)

# Filler sounds. Word-boundary matched, case-insensitive.
_FILLERS_RE = re.compile(
    r"\b(?:um+|uh+|erm+|hmm+|mhm+|э-?э+|эм+|м-?м+|ммм+|а-?а+э?)\b[,.]?\s*",
    re.IGNORECASE,
)

# Spoken punctuation commands. Order matters: longer phrases first.
# Whisper often writes the command with its own punctuation ("запятая,"),
# so surrounding commas/periods around the command are consumed too.
_SPOKEN = [
    # Russian
    (r"с\s+новой\s+строки|новая\s+строка", "\n"),
    (r"новый\s+абзац|с\s+нового\s+абзаца", "\n\n"),
    (r"вопросительный\s+знак|знак\s+вопроса", "?"),
    (r"восклицательный\s+знак", "!"),
    (r"точка\s+с\s+запятой", ";"),
    (r"двоеточие", ":"),
    (r"запятая", ","),
    (r"многоточие", "…"),
    (r"точка", "."),
    (r"тире", "—"),
    (r"открыть\s+скобку", "("),
    (r"закрыть\s+скобку", ")"),
    (r"открыть\s+кавычки", "«"),
    (r"закрыть\s+кавычки", "»"),
    # English
    (r"new\s+line", "\n"),
    (r"new\s+paragraph", "\n\n"),
    (r"question\s+mark", "?"),
    (r"exclamation\s+(?:mark|point)", "!"),
    (r"semicolon", ";"),
    (r"colon", ":"),
    (r"comma", ","),
    (r"ellipsis", "…"),
    (r"period|full\s+stop", "."),
    (r"dash", "—"),
    (r"open\s+paren(?:thesis)?", "("),
    (r"close\s+paren(?:thesis)?", ")"),
    (r"open\s+quotes?", "“"),
    (r"close\s+quotes?", "”"),
]
_SPOKEN_RES = [
    (re.compile(r"[,.\s]*\b(?:%s)\b[,.]?" % pat, re.IGNORECASE), repl)
    for pat, repl in _SPOKEN
]

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")
_END_PUNCT = ".!?…:;,—-\n"


def initial_prompt(language, custom_words=""):
    """Build the initial prompt: punctuation style nudge + custom vocabulary.

    With auto language detection a fixed-language prompt would bias detection,
    so only the vocabulary (if any) is used there.
    """
    parts = []
    base = _PROMPTS.get(language)
    if base:
        parts.append(base)
    words = ", ".join(w.strip() for w in (custom_words or "").split(",") if w.strip())
    if words:
        parts.append(words + ".")
    return " ".join(parts) or None


def _drop_hallucinations(text):
    kept = []
    for sentence in _SENT_SPLIT_RE.split(text):
        low = sentence.lower()
        if any(h in low for h in _HALLUCINATIONS):
            continue
        kept.append(sentence)
    return " ".join(kept)


def _apply_spoken_punctuation(text):
    for rx, repl in _SPOKEN_RES:
        text = rx.sub(repl, text)
    return text


def _normalize(text):
    # Collapse runs of spaces (but keep newlines from "new line" commands).
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    # No space before punctuation, single space after where a word follows.
    text = re.sub(r"\s+([,.!?…;:%)»])", r"\1", text)
    text = re.sub(r"([«(])\s+", r"\1", text)
    text = re.sub(r"([,.!?…;:])(?=[^\s\d,.!?…;:)»\n])", r"\1 ", text)
    # Collapse duplicated punctuation like ",," or ".," left by replacements.
    text = re.sub(r"([,.!?;:])(?:\s*[,.])+", r"\1", text)
    return text.strip()


def _capitalize_sentences(text):
    def up(m):
        return m.group(1) + m.group(2).upper()
    text = re.sub(r"([.!?…]\s+|\n)(\w)", up, text)
    return text[0].upper() + text[1:] if text else text


def clean(text, spoken_punctuation=False, ensure_period=True):
    """Full post-processing pipeline for one transcription."""
    if not text:
        return text
    text = _drop_hallucinations(text)
    text = _FILLERS_RE.sub("", text)
    if spoken_punctuation:
        text = _apply_spoken_punctuation(text)
    text = _normalize(text)
    text = _capitalize_sentences(text)
    if ensure_period and len(text) > 2 and text[-1] not in _END_PUNCT:
        text += "."
    return text
