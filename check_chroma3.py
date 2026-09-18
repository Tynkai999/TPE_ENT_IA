import chromadb
client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection("ent_documents")
results = collection.query(query_texts=["bouton se connecter"], n_results=5)
for i, doc in enumerate(results['documents'][0]):
    print(f"--- Chunk {i} ---")
    print(doc)
