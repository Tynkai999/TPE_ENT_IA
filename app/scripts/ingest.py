from app.rag.ingestion import ingest_all


if __name__ == "__main__":
    result = ingest_all()

    if not result:
        print("Aucun document trouvé dans data/documents/")
    else:
        total_ingested = 0
        total_ignored = 0
        
        for filename, data in result.items():
            status = data.get("status")
            chunks = data.get("chunks", 0)
            
            if status == "ignored":
                print(f"[-] IGNORÉ : {filename} (déjà ingéré)")
                total_ignored += 1
            else:
                print(f"[+] INGÉRÉ : {filename} ({chunks} chunks indexés)")
                total_ingested += 1
                
        print("\n--- Résumé ---")
        print(f"Fichiers ingérés : {total_ingested}")
        print(f"Fichiers ignorés : {total_ignored}")
