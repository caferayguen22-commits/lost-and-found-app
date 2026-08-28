import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "chroma_store")
COLLECTION_NAME = "items"
EMBEDDING_MODEL = "text-embedding-3-small"

_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
_vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=_embeddings,
    persist_directory=CHROMA_DB_PATH,
    # Cosine-Distanz statt Chromas Standard-L2 -- gibt uns einen 0..1-artigen
    # Ähnlichkeitswert (1 - Distanz), der sich intuitiv als Schwellwert nutzen lässt.
    collection_metadata={"hnsw:space": "cosine"},
)


def _embedding_text(title: str, description: str) -> str:
    """Was tatsächlich embedded wird -- NIE secret_feature, nur Titel + Beschreibung.
    Kategorie fließt bewusst NICHT in den Text ein, sondern ausschließlich als
    Metadaten-Filter (siehe find_similar_candidates) -- so bleibt der Text bei
    einer kategorie-freien Suche (Retry-Strategie) konsistent zu dem, was
    ursprünglich indiziert wurde."""
    return f"{title} -- {description}"


def index_item(item) -> None:
    """
    Fügt das Embedding eines Items hinzu bzw. aktualisiert es. Idempotent:
    löscht einen evtl. vorhandenen alten Eintrag zuerst, damit ein erneuter
    Aufruf (z.B. nach einer akzeptierten Rechtschreibkorrektur) sauber
    ersetzt statt zu duplizieren.
    """
    doc_id = str(item.id)
    remove_item(item.id)
    _vector_store.add_texts(
        texts=[_embedding_text(item.title, item.description)],
        metadatas=[{
            "item_id": item.id,
            "type": item.type,
            "category": item.category,
            "match_found": bool(item.match_found),
        }],
        ids=[doc_id],
    )


def remove_item(item_id: int) -> None:
    """Löscht ein Item aus dem Vektor-Index (z.B. beim Löschen des Items selbst).
    Gefahrlos, auch wenn die ID gar nicht existiert."""
    _vector_store.delete(ids=[str(item_id)])


def find_similar_candidates(opposite_type: str, category: str, title: str, description: str,
                             k: int = 5, require_category: bool = True) -> list[dict]:
    """
    Ähnlichkeitssuche gegen offene (match_found=False) Items des Gegentyps.
    Gibt eine nach Ähnlichkeit sortierte Liste von {"item_id", "similarity"}
    zurück -- similarity ist 1 minus Cosine-Distanz, höher = ähnlicher.
    """
    conditions = [
        {"type": {"$eq": opposite_type}},
        {"match_found": {"$eq": False}},
    ]
    if require_category:
        conditions.append({"category": {"$eq": category}})
    filter_dict = {"$and": conditions}

    query_text = _embedding_text(title, description)
    results = _vector_store.similarity_search_with_score(query_text, k=k, filter=filter_dict)

    return [
        {"item_id": doc.metadata["item_id"], "similarity": 1 - distance}
        for doc, distance in results
    ]
