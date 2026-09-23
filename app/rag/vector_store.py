from langchain_chroma import Chroma

from app.core.config import settings
from app.rag.embeddings import get_embeddings


def get_vector_store() -> Chroma:
    return Chroma(
        collection_name="ent_documents",
        persist_directory=settings.chroma_dir,
        embedding_function=get_embeddings(),
    )


def check_hash_exists(file_hash: str) -> bool:
    """Vérifie si un fichier avec ce hash a déjà été ingéré."""
    store = get_vector_store()
    results = store.get(where={"file_hash": file_hash}, limit=1)
    return len(results.get("ids", [])) > 0


def get_known_platforms() -> set:
    """Retourne l'ensemble des noms de plateformes (en majuscules) présentes dans ChromaDB."""
    try:
        store = get_vector_store()
        all_data = store.get()
        return {
            m.get("platform", "").upper()
            for m in all_data.get("metadatas", [])
            if m and m.get("platform") and m.get("platform") != "unknown"
        }
    except Exception:
        return set()

