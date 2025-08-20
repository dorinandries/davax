from pathlib import Path
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from .config import settings

# Ancorează path-ul de folderul backend, nu de CWD
BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend/app -> parent = .../backend
PERSIST_PATH = str(BASE_DIR / "chroma")

chroma_client = PersistentClient(path=PERSIST_PATH)

embedder = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.openai_api_key,
    model_name=settings.embedding_model,
)

COLLECTION = "books"

def get_collection():
    try:
        return chroma_client.get_collection(COLLECTION, embedding_function=embedder)
    except Exception:
        return chroma_client.create_collection(COLLECTION, embedding_function=embedder)

def reset_collection():
    try:
        chroma_client.delete_collection(COLLECTION)
    except Exception:
        pass
    return chroma_client.create_collection(COLLECTION, embedding_function=embedder)