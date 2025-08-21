
import re

RE_CODE = re.compile(r"\b(python|javascript|typescript|react|vite|angular|vue|sql|bash|docker|kubernetes|algoritm|func(ț|t)ie|function|script|cod)\b", re.I)
RE_PAGES = re.compile(r"\b(c(â|a)te|care este num(ă|a)rul de)\s+pagini\b|\bpagini\s+are\b", re.I)
RE_AUTHOR = re.compile(r"\b(autorul|cine a scris|de cine e scris)\b", re.I)
RE_YEAR = re.compile(r"\b(anul apari(t|ț)iei|c(â|a)nd a fost publicat(ă|a)?)\b", re.I)
RE_THIS_BOOK = re.compile(r"\b(aceast(ă|a)\s+carte|cartea\s+asta|despre\s+ea|despre\s+aceast(ă|a))\b", re.I)
RE_ORDINAL = re.compile(r"\b(prim(a|ă)|a\s+doua|a\s+treia|a\s+patra)\b", re.I)

def classify(query: str) -> str:
    q = query or ""
    if RE_CODE.search(q):
        return "out_of_scope"
    if RE_ORDINAL.search(q):
        return "ordinal"
    if RE_PAGES.search(q) or RE_AUTHOR.search(q) or RE_YEAR.search(q) or RE_THIS_BOOK.search(q):
        return "book_followup"
    return "recommendation"
