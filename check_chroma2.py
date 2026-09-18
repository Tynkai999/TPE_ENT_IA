import chromadb
client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection("ent_documents")
docs = collection.get()
found_annex = False
for doc in docs['documents']:
    if "ANNEXE VISUELLE" in doc:
        print("Annexe Visuelle trouvée !!")
        found_annex = True
        break
if not found_annex:
    print("Aucune Annexe Visuelle trouvée dans ChromaDB.")
