import chromadb
client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection("ent_documents")
results = collection.query(query_texts=["bouton"], n_results=10)
for doc in results['documents'][0]:
    if "ANNEXE VISUELLE" in doc or "Image" in doc:
        print(doc)
