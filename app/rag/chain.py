from typing import Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.prompts import RAG_PROMPT, SYSTEM_PROMPT
from app.llm.provider import get_llm
from app.rag.retriever import retrieve


def format_documents(documents) -> str:
    if not documents:
        return "Aucun document pertinent n'a été trouvé."

    parts = []
    for doc in documents:
        platform = doc.metadata.get("platform", "inconnue")
        version = doc.metadata.get("version", "inconnue")
        source = doc.metadata.get("source", "document inconnu")
        page = doc.metadata.get("page")
        
        location = f"Application {platform} v{version} (Fichier: {source}"
        if page is not None:
            location += f", page {page + 1}"
        location += ")"
        
        parts.append(f"[Source: {location}]\n{doc.page_content}")

    return "\n\n---\n\n".join(parts)


def answer_question(messages: list, platform: Optional[str] = None):
    # Extraire la dernière question pour le RAG Retriever
    from langchain_core.messages import HumanMessage
    
    last_question = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_question = msg.content
            break
            
    documents = retrieve(last_question, platform=platform)
    context = format_documents(documents)

    # Convertir les messages en format ChatPromptTemplate
    # On ajoute le System Prompt avec le Contexte RAG au début
    prompt_messages = [("system", SYSTEM_PROMPT + "\n\n" + RAG_PROMPT)]
    
    # On ajoute l'historique (limité aux 10 derniers pour ne pas surcharger)
    recent_messages = messages[-10:]
    for msg in recent_messages:
        role = "human" if isinstance(msg, HumanMessage) else "ai"
        prompt_messages.append((role, msg.content))

    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = prompt | get_llm() | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
        }
    )

    # Déduplication des sources uniquement si la réponse est positive (non-refus)
    unique_sources = []
    
    refusal_keywords = [
        "ne dispose pas",
        "n'ai pas d'information",
        "n'ai pas d'info",
        "pas d'informations spécifiques",
        "ne peux pas vous aider",
        "ne peux pas vous donner",
        "ne peux pas fournir",
        "ne peux pas",
        "ne connais pas",
        "aucun document",
        "dépasse mes capacités",
        "n'est pas disponible",
        "documentation officielle",
        "site officiel",
        "sort de mon champ",
        "leur support technique",
    ]
    is_refusal = any(kw in answer.lower() for kw in refusal_keywords)
    
    if not is_refusal:
        seen = set()
        for doc in documents:
            src = doc.metadata.get("source")
            page_val = doc.metadata.get("page")
            page = page_val + 1 if page_val is not None else None
            
            identifier = (src, page)
            if identifier not in seen:
                seen.add(identifier)
                unique_sources.append({
                    "source": src,
                    "page": page
                })

    return answer, unique_sources

