import chromadb
client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection("ent_documents")
results = collection.query(query_texts=["Quels sont les champs de la section de saisie des informations personnelles et administratives (numéro WhatsApp) ?"], n_results=1)
print(results['documents'][0][0])
