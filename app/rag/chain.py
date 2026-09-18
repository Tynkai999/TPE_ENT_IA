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


def answer_question(question: str, platform: Optional[str] = None):
    documents = retrieve(question, platform=platform)
    context = format_documents(documents)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT + "\n\n" + RAG_PROMPT),
            ("human", "{question}"),
        ]
    )

    chain = prompt | get_llm() | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    # Déduplication des sources
    unique_sources = []
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
