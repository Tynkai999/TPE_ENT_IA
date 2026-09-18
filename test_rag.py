import sys
from app.rag.retriever import retrieve
from app.rag.chain import answer_question

print("Test Retrieve sans filtre:")
docs = retrieve("Hello")
print(f"Trouvé {len(docs)} documents.")

print("\nTest Retrieve avec filtre existant (Produits):")
docs = retrieve("Hello", platform="Produits")
print(f"Trouvé {len(docs)} documents.")

print("\nTest Retrieve avec filtre non-existant (Inconnu):")
docs = retrieve("Hello", platform="Inconnu")
print(f"Trouvé {len(docs)} documents.")
