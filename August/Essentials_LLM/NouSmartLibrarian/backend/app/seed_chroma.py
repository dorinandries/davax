from pathlib import Path
import re, json
from .rag import add_books

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _from_md(md_text: str):
    # parse blocuri de forma:
    # ## Title: X
    # <rezumat multiline>
    # Teme: a, b, c
    items = []
    blocks = re.split(r'^##\s*Title:\s*', md_text, flags=re.M)
    for b in blocks[1:]:
        title, rest = b.split('\n', 1)
        # rezumat = tot până la linia "Teme:" (dacă există)
        parts = rest.strip().splitlines()
        summary_lines = []
        themes = []
        for line in parts:
            if line.strip().lower().startswith('teme:'):
                themes = [t.strip() for t in line.split(':',1)[1].split(',') if t.strip()]
                break
            summary_lines.append(line)
        summary = ' '.join(l.strip() for l in summary_lines).strip()
        items.append((title.strip(), summary, themes))
    return items

def run():
    md = (DATA_DIR / "book_summaries.md").read_text(encoding="utf-8")
    items = _from_md(md)
    # dacă ai și JSON-ul cu rezumate complete, nu schimbă RAG; tool-ul îl folosește separat
    add_books(items)
    print(f"Seeded {len(items)} items into Chroma.")

if __name__ == "__main__":
    run()