"""
CLI de test pour l'Agent Multi-Agent avec Mémoire.
Chaque session conserve l'historique de la conversation.
"""
import sys
import uuid

from app.core.agent import run_agent


def main():
    print("=" * 50)
    print("  Assistant ENT - Tech Pole Expertise (TPE)")
    print("  Agent Multi-Agent avec Mémoire")
    print("=" * 50)
    print("Vérifiez que LM Studio est bien lancé en arrière-plan.")
    print("Tapez 'q' pour quitter, 'reset' pour effacer la mémoire.\n")
    
    # Chaque session a un identifiant unique (pour la mémoire)
    thread_id = str(uuid.uuid4())[:8]
    print(f"[Session: {thread_id}] Mémoire activée.\n")
    
    while True:
        try:
            question = input("Vous : ")
            if question.strip().lower() in ['q', 'quit', 'exit']:
                print("\nAu revoir ! 👋")
                break
            
            if question.strip().lower() == 'reset':
                thread_id = str(uuid.uuid4())[:8]
                print(f"\n[Mémoire effacée] Nouvelle session : {thread_id}\n")
                continue
                
            if not question.strip():
                continue
            
            print("\n[Exécution de l'Agent]")
            
            # Appel au graphe multi-agent avec mémoire
            answer, sources = run_agent(question, thread_id=thread_id)
            
            print("\n" + "=" * 40)
            print("RÉPONSE :")
            print(answer)
            
            if sources:
                print("\nSOURCES DÉDUPLIQUÉES :")
                for idx, src in enumerate(sources):
                    page_info = f", page {src['page']}" if src.get('page') else ""
                    print(f"  [{idx + 1}] Fichier: {src['source']}{page_info}")
            print("=" * 40 + "\n")

        except KeyboardInterrupt:
            print("\n\nAu revoir ! 👋")
            break
        except Exception as e:
            print(f"\n[ERREUR] {e}\n")


if __name__ == "__main__":
    main()
