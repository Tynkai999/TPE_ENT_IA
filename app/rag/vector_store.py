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
