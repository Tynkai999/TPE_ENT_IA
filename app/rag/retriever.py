"""
Retriever Hybride : BM25 (mots-clés) + Vecteurs (sémantique) + CrossEncoder (reranking).

Architecture en 3 étapes :
1. Recherche par mots-clés stricts (BM25) → trouve les documents contenant exactement les termes.
2. Recherche sémantique (Vecteurs ChromaDB) → trouve les documents au sens proche.
3. Fusion + Reranking (CrossEncoder) → trie les résultats fusionnés par pertinence réelle.
"""
from typing import Optional, List
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.vector_store import get_vector_store

# Initialisation du reranker (sera téléchargé au premier appel si non présent)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)


def _get_bm25_results(question: str, platform: Optional[str] = None, k: int = 10) -> List[Document]:
    """
    Recherche par mots-clés stricts via BM25.
    Charge tous les documents depuis ChromaDB puis applique BM25 en mémoire.
    """
    store = get_vector_store()
    
    # Récupérer tous les documents de la collection (avec filtre optionnel)
    filter_kwargs = {}
    if platform:
        filter_kwargs["where"] = {"platform": platform}
    
    all_data = store.get(**filter_kwargs)
    
    if not all_data["documents"]:
        return []
    
    # Reconstruire les objets Document
    all_docs = []
    for i, content in enumerate(all_data["documents"]):
        metadata = all_data["metadatas"][i] if all_data["metadatas"] else {}
        all_docs.append(Document(page_content=content, metadata=metadata))
    
    # Tokeniser pour BM25
    tokenized_corpus = [doc.page_content.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # Chercher
    tokenized_query = question.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    # Associer scores et documents, trier par score décroissant
    doc_scores = list(zip(all_docs, scores))
    doc_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Retourner les k meilleurs (avec un score > 0)
    return [doc for doc, score in doc_scores[:k] if score > 0]


def _get_vector_results(question: str, platform: Optional[str] = None, k: int = 10) -> List[Document]:
    """
    Recherche sémantique via les vecteurs ChromaDB (embeddings).
    """
    filter_kwargs = {}
    if platform:
        filter_kwargs["filter"] = {"platform": platform}

    return get_vector_store().similarity_search(
        question,
        k=k,
        **filter_kwargs
    )


def _deduplicate_docs(docs: List[Document]) -> List[Document]:
    """
    Supprime les doublons basés sur le contenu textuel.
    """
    seen_contents = set()
    unique = []
    for doc in docs:
        content_hash = hash(doc.page_content)
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            unique.append(doc)
    return unique


def retrieve(question: str, platform: Optional[str] = None) -> List[Document]:
    """
    Point d'entrée principal du retriever hybride.
    
    1. Lance BM25 et la recherche vectorielle en parallèle.
    2. Fusionne et déduplique les résultats.
    3. Applique le CrossEncoder pour trier par pertinence réelle.
    4. Retourne les top_k meilleurs documents.
    """
    initial_k = max(10, settings.top_k * 3)
    
    # Étape 1 : Double recherche
    bm25_docs = _get_bm25_results(question, platform=platform, k=initial_k)
    vector_docs = _get_vector_results(question, platform=platform, k=initial_k)
    
    # Étape 2 : Fusion + déduplication
    combined = bm25_docs + vector_docs
    combined = _deduplicate_docs(combined)
    
    if not combined:
        return []
    
    # Étape 3 : Reranking via CrossEncoder
    pairs = [[question, doc.page_content] for doc in combined]
    scores = reranker.predict(pairs)
    
    doc_score_pairs = list(zip(combined, scores))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Étape 4 : Ne conserver que les top_k
    top_docs = [doc for doc, score in doc_score_pairs[:settings.top_k]]
    
    return top_docs
