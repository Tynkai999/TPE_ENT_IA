"""
Agent Multi-Agent avec Mémoire (LangGraph).

Architecture :
- Un graphe d'état (StateGraph) qui conserve l'historique des messages.
- 3 nœuds (agents) :
  1. Router : Analyse l'intention de l'utilisateur (RAG ou API).
  2. RAG Agent : Cherche dans la documentation et génère une réponse.
  3. API Agent : Interroge le système ENT en temps réel.
"""
from typing import TypedDict, Annotated, Optional, Sequence
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from app.core.prompts import INTENT_DETECTION_PROMPT, SYSTEM_PROMPT, RAG_PROMPT
from app.llm.provider import get_llm
from app.rag.chain import answer_question
from app.core.tools import get_user_info_tool, list_accessible_platforms_tool


# ─── État partagé entre tous les nœuds ───────────────────────────
class AgentState(TypedDict):
    """
    L'état du graphe. Le champ 'messages' est la MÉMOIRE de la conversation.
    Grâce à l'annotation 'add_messages', chaque nouveau message est
    automatiquement ajouté à l'historique au lieu de le remplacer.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    intent: Optional[str]
    platform: Optional[str]
    answer: Optional[str]
    sources: Optional[list]


# ─── Nœud 1 : Le Routeur (Cerveau) ──────────────────────────────
def router_node(state: AgentState) -> dict:
    """
    Analyse la dernière question de l'utilisateur pour déterminer
    s'il faut utiliser le RAG ou l'API.
    Utilise l'historique de la conversation pour mieux comprendre le contexte.
    """
    messages = state["messages"]
    
    # Extraire la dernière question humaine
    last_question = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_question = msg.content
            break
    
    # Construire un résumé de l'historique pour aider le routeur
    history_summary = ""
    recent_messages = messages[-6:]  # Les 3 derniers échanges (question + réponse)
    for msg in recent_messages:
        if isinstance(msg, HumanMessage):
            history_summary += f"Utilisateur : {msg.content}\n"
        elif isinstance(msg, AIMessage):
            # On tronque la réponse pour ne pas surcharger le routeur
            truncated = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
            history_summary += f"Assistant : {truncated}\n"
            
    if not history_summary.strip():
        history_summary = "(Aucun échange précédent, début de la conversation)\n"
    
    prompt = PromptTemplate(
        template=INTENT_DETECTION_PROMPT,
        input_variables=["question", "history"],
    )
    
    chain = prompt | get_llm() | JsonOutputParser()
    
    print(f"[Agent] Analyse de l'intention pour : '{last_question}'")
    
    try:
        result = chain.invoke({"question": last_question, "history": history_summary})
        intent = result.get("intent", "rag").lower()
        if intent not in ["rag", "api"]:
            intent = "rag"
            
        platform = result.get("platform")
        if isinstance(platform, str) and platform.lower() in ["null", "none", "", "null"]:
            platform = None
            
        print(f"[Agent] Intention détectée : {intent.upper()} (Plateforme: {platform})")
        
        return {"intent": intent, "platform": platform}
        
    except Exception as e:
        print(f"[Agent] Erreur de détection d'intention : {e}")
        return {"intent": "rag", "platform": None}


# ─── Nœud 2 : L'Agent Documentaliste (RAG) ──────────────────────
def rag_node(state: AgentState) -> dict:
    """
    Cherche dans la documentation (ChromaDB) et génère une réponse
    contextualisée en tenant compte de l'historique.
    """
    from app.rag.vector_store import get_known_platforms
    
    messages = state["messages"]
    platform = state.get("platform")
    
    # 1. Vérification préventive anti-hallucination :
    # Si l'utilisateur demande une plateforme spécifique qui n'existe pas dans l'ENT,
    # on refuse immédiatement sans chercher ni laisser le LLM deviner.
    known_platforms = get_known_platforms()
    if platform and known_platforms:
        # Correspondance insensible à la casse
        if platform.upper() not in known_platforms:
            answer = f"Je ne dispose pas d'informations sur la solution '{platform}' au sein de l'Espace Numérique de Travail (ENT) de Tech Pole Expertise."
            return {
                "messages": [AIMessage(content=answer)],
                "answer": answer,
                "sources": [],
            }
    
    # Extraire la dernière question
    last_question = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_question = msg.content
            break
    
    # Générer la réponse via le RAG existant avec l'historique complet
    answer, sources = answer_question(messages, platform=platform)
    
    return {
        "messages": [AIMessage(content=answer)],
        "answer": answer,
        "sources": sources,
    }


# ─── Nœud 3 : L'Agent Technique (API Temps Réel) ────────────────
def api_node(state: AgentState) -> dict:
    """
    Interroge le système ENT en temps réel via les outils LangChain.
    """
    messages = state["messages"]
    
    # Extraire la dernière question
    last_question = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_question = msg.content
            break
    
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
        max_iterations=5,
    )
    
    try:
        result = agent_executor.invoke({"input": last_question})
        answer = result["output"]
    except Exception as e:
        print(f"[Agent] Erreur d'exécution de l'outil : {e}")
        answer = "Désolé, une erreur technique m'empêche d'interroger le système en temps réel."
    
    return {
        "messages": [AIMessage(content=answer)],
        "answer": answer,
        "sources": [],
    }


# ─── Fonction de routage conditionnel ────────────────────────────
def route_intent(state: AgentState) -> str:
    """
    Décide vers quel nœud envoyer la requête après le routeur.
    """
    intent = state.get("intent", "rag")
    if intent == "api":
        return "api_agent"
    return "rag_agent"


# ─── Construction du Graphe ──────────────────────────────────────
def build_graph():
    """
    Construit le graphe LangGraph avec mémoire.
    
    Flot :
        [Utilisateur] → Router → (RAG ou API) → [Réponse]
    """
    graph = StateGraph(AgentState)
    
    # Ajouter les 3 nœuds (agents)
    graph.add_node("router", router_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("api_agent", api_node)
    
    # Définir le point d'entrée
    graph.set_entry_point("router")
    
    # Routage conditionnel après le routeur
    graph.add_conditional_edges(
        "router",
        route_intent,
        {
            "rag_agent": "rag_agent",
            "api_agent": "api_agent",
        }
    )
    
    # Les deux agents terminent la conversation (fin du graphe)
    graph.add_edge("rag_agent", END)
    graph.add_edge("api_agent", END)
    
    # Compiler avec la mémoire persistante
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ─── Singleton du graphe ─────────────────────────────────────────
_graph = None

def get_graph():
    """Retourne l'instance unique du graphe compilé."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ─── Point d'entrée principal ────────────────────────────────────
def run_agent(question: str, thread_id: str = "default") -> tuple:
    """
    Envoie une question au graphe multi-agent.
    
    Args:
        question: La question de l'utilisateur.
        thread_id: Identifiant de la conversation (pour la mémoire).
                   Chaque thread_id a son propre historique.
    
    Returns:
        (answer, sources) - La réponse et les sources documentaires.
    """
    graph = get_graph()
    
    # Configurer le thread (chaque utilisateur peut avoir sa propre conversation)
    config = {"configurable": {"thread_id": thread_id}}
    
    # Exécuter le graphe
    result = graph.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config,
    )
    
    answer = result.get("answer", "Désolé, je n'ai pas pu générer de réponse.")
    sources = result.get("sources", [])
    
    return answer, sources
