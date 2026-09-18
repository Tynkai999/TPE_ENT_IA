import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from app.core.prompts import INTENT_DETECTION_PROMPT, SYSTEM_PROMPT
from app.llm.provider import get_llm
from app.rag.chain import answer_question
from app.core.tools import get_user_info_tool, list_accessible_platforms_tool


def detect_intent(question: str) -> dict:
    """
    Analyse la question pour déterminer si on doit utiliser le RAG ou l'API.
    Retourne un dictionnaire : {"intent": "rag" | "api", "platform": "..." | None}
    """
    prompt = PromptTemplate(
        template=INTENT_DETECTION_PROMPT,
        input_variables=["question"],
    )
    
    # JsonOutputParser force LangChain à parser la réponse comme du JSON
    chain = prompt | get_llm() | JsonOutputParser()
    
    try:
        result = chain.invoke({"question": question})
        # Nettoyage de base au cas où le LLM renvoie des formats un peu libres
        intent = result.get("intent", "rag").lower()
        if intent not in ["rag", "api"]:
            intent = "rag"
            
        platform = result.get("platform")
        if isinstance(platform, str) and platform.lower() == "null":
            platform = None
            
        return {"intent": intent, "platform": platform}
        
    except Exception as e:
        # En cas d'erreur de parsing JSON, on fallback sur le RAG par sécurité
        print(f"[Agent] Erreur de détection d'intention : {e}")
        return {"intent": "rag", "platform": None}


def run_api_agent(question: str) -> str:
    llm = get_llm()
    tools = [get_user_info_tool, list_accessible_platforms_tool]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + "\n\nTu disposes d'outils pour récupérer des informations système."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        max_iterations=5
    )
    
    try:
        result = agent_executor.invoke({"input": question})
        return result["output"]
    except Exception as e:
        print(f"[Agent] Erreur d'exécution de l'outil : {e}")
        return "Désolé, une erreur technique m'empêche d'interroger le système en temps réel."


def run_agent(question: str):
    """
    Le cœur de l'agent. Route la question vers le bon composant.
    Retourne (answer, sources)
    """
    print(f"[Agent] Analyse de l'intention pour : '{question}'")
    intent_data = detect_intent(question)
    
    intent = intent_data["intent"]
    platform = intent_data["platform"]
    
    print(f"[Agent] Intention détectée : {intent.upper()} (Plateforme: {platform})")
    
    if intent == "rag":
        return answer_question(question, platform=platform)
    elif intent == "api":
        answer = run_api_agent(question)
        return answer, []
    else:
        return "Erreur interne : Intention inconnue.", []
