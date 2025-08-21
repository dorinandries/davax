
import re
OBSCENE = {"cur", "pula", "dracu", "morții", "mortii", "futu", "bou", "handicapat", "tâmpit", "tampit"}

def is_offensive(s: str) -> bool:
    text = (s or "").lower()
    words = set(re.findall(r"[a-zăâîșț\-]+", text))
    return any(w in OBSCENE for w in words)
