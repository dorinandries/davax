from typing import List, Tuple, Any
from .chroma_setup import get_collection
from .tokens_logger import log_embedding

def add_books(items: List[Tuple[str, str, List[str]]]):
    coll = get_collection()
    ids, docs, metadatas = [], [], []
    for (title, summary, themes) in items:
        ids.append(f"book_{title}")
        docs.append(f"Title: {title}\nThemes: {', '.join(themes)}\nSummary: {summary}")
        metadatas.append({
            "title": title,
            "themes": ", ".join(themes)
        })
    # estimare pt log de embedding (Chroma face embeddings intern)
    est_tokens = sum(int(len(d.split()) * 1.3) for d in docs)
    log_embedding(user="system", input_preview="init_books", tokens=est_tokens)
    coll.upsert(ids=ids, documents=docs, metadatas=metadatas)

def _themes_to_list(v: Any):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [t.strip() for t in v.split(",") if t.strip()]
    return []

def retrieve(query, k=3):
    coll = get_collection()
    results = coll.query(query_texts=[query], n_results=k, include=["metadatas", "documents"])
    contexts = []
    for doc, meta in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]):
        contexts.append({
            "chunk": doc,
            "title":  (meta or {}).get("title", "")
        })
    return contexts


def count_books() -> int:
    coll = get_collection()
    try:
        return coll.count()
    except Exception:
        return 0