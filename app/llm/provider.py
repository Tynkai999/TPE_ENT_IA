from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm() -> ChatOpenAI:
    # LM Studio expose une API compatible avec les clients OpenAI.
    # Cela permet de garder le RAG indépendant du fournisseur de LLM.
    return ChatOpenAI(
        model=settings.lm_model,
        base_url=settings.lm_base_url,
        api_key=settings.lm_api_key,
        temperature=0.2,
    )
