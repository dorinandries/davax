import re


# Listă simplă (RO+EN). Extinde după nevoie.
OBSCENE = [
r"\bcur\b", r"\bpula\b", r"\bmuie\b", r"\bpizd\w*\b",
r"\bfuck\b", r"\bshit\b", r"\basshole\b", r"\bcunt\b"
]


pat = re.compile("|".join(OBSCENE), flags=re.IGNORECASE)


def is_offensive(text: str) -> bool:
    return bool(pat.search(text or ""))