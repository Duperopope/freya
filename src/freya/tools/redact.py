import re

_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bgho_[A-Za-z0-9]+\b"),
    re.compile(r"\bghu_[A-Za-z0-9]+\b"),
    re.compile(r"\bghs_[A-Za-z0-9]+\b"),
    re.compile(r"\bghr_[A-Za-z0-9]+\b"),
]

def redact_secrets(text: str) -> str:
    out = text
    for pat in _PATTERNS:
        out = pat.sub("[REDACTED_SECRET]", out)
    return out
