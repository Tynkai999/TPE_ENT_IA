"""
CLI de test pour l'Agent Multi-Agent avec Mémoire.
Chaque session conserve l'historique de la conversation.
L'ingestion des nouveaux documents se fait automatiquement au démarrage.
"""
import sys
import uuid

from app.core.agent import run_agent
from app.rag.ingestion import ingest_all


def auto_ingest():
    """
    Vérifie s'il y a de nouveaux documents dans data/documents/ et les ingère.
    Les fichiers déjà ingérés sont automatiquement ignorés (hash).
    """
    print("[Auto-Ingest] Vérification des nouveaux documents...")
    result = ingest_all()

    if not result:
        print("[Auto-Ingest] Aucun document trouvé dans data/documents/\n")
        return

    new_count = 0
    for filename, data in result.items():
        if data.get("status") == "ingested":
            chunks = data.get("chunks", 0)
            print(f"  [+] NOUVEAU : {filename} ({chunks} chunks indexés)")
            new_count += 1

    if new_count == 0:
        print("[Auto-Ingest] Tous les documents sont déjà à jour. ✅\n")
    else:
        print(f"[Auto-Ingest] {new_count} nouveau(x) document(s) ingéré(s). ✅\n")


def main():
    print("=" * 50)
    print("  Assistant ENT - Tech Pole Expertise (TPE)")
    print("  Agent Multi-Agent avec Mémoire")
    print("=" * 50)
    print("Vérifiez que LM Studio est bien lancé en arrière-plan.\n")

    # Auto-ingestion des nouveaux documents au démarrage
    auto_ingest()

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
