from typing import Optional
from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.rag.vector_store import get_vector_store

# Initialisation du reranker (sera téléchargé au premier appel si non présent)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)


def retrieve(question: str, platform: Optional[str] = None):
    # 1. Filtrage optionnel
    filter_kwargs = {}
    if platform:
        filter_kwargs["filter"] = {"platform": platform}
        
    # On récupère plus de documents au départ pour le reranking
    initial_k = max(10, settings.top_k * 2)

    docs = get_vector_store().similarity_search(
        question,
        k=initial_k,
        **filter_kwargs
    )
    
    if not docs:
        return []

    # 2. Reranking
    pairs = [[question, doc.page_content] for doc in docs]
    scores = reranker.predict(pairs)
    
    # Associer les scores aux documents
    doc_score_pairs = list(zip(docs, scores))
    
    # Trier par score décroissant
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Ne conserver que les top_k
    top_docs = [doc for doc, score in doc_score_pairs[:settings.top_k]]
    
    return top_docs
