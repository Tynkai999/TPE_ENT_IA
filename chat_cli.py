import sys

from app.core.agent import run_agent

def main():
    print("=== Test de l'Agent Core (Phase 3) ===")
    print("Vérifiez que LM Studio est bien lancé en arrière-plan.\n")
    
    while True:
        try:
            question = input("\nVotre question (ou 'q' pour quitter) : ")
            if question.lower() in ['q', 'quit', 'exit']:
                break
                
            print("\n[Exécution de l'Agent]")
            
            # Appel au routeur de l'agent
            answer, sources = run_agent(question)
            
            print("\n" + "="*40)
            print("RÉPONSE :")
            print(answer)
            print("\nSOURCES DÉDUPLIQUÉES :")
            for idx, src in enumerate(sources):
                page_info = f", page {src['page']}" if src['page'] else ""
                print(f"  [{idx + 1}] Fichier: {src['source']}{page_info}")
            print("="*40)

        except Exception as e:
            print(f"\n[ERREUR] Une erreur est survenue (Avez-vous bien lancé LM Studio sur le port 1234 ?) : {e}")

if __name__ == "__main__":
    main()

