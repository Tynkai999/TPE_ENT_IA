import hashlib
import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.vector_store import get_vector_store, check_hash_exists


def calculate_hash(file_path: Path) -> str:
    """Calcule le hash SHA-256 d'un fichier."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

def extract_metadata_from_filename(filename: str) -> dict:
    """Extrait la plateforme et la version du nom de fichier."""
    # Ex: Manuel_Produits_v1.2.pdf ou APEC Manuel d'utilisation admin.docx
    # On va essayer de parser au mieux, sinon "unknown"
    match_v = re.search(r'_v([0-9\.]+)', filename)
    version = match_v.group(1) if match_v else "unknown"
    
    # Pour la plateforme, essayons de déduire du nom (ex: "Produits", "APEC")
    platform = "unknown"
    if "Produit" in filename: platform = "Produits"
    elif "APEC" in filename.upper() or "Apec" in filename: platform = "APEC"
    elif "Ventes" in filename: platform = "Ventes"
    
    return {
        "platform": platform,
        "version": version
    }

def clean_text(text: str) -> str:
    """Nettoie le texte extrait."""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

import tempfile
import shutil
import docx2txt
from app.rag.vision import process_document_images

def load_document(path: Path) -> list[Document]:
    if path.suffix.lower() == '.pdf':
        return PyPDFLoader(str(path)).load()
    elif path.suffix.lower() == '.docx':
        img_dir = Path(tempfile.mkdtemp(prefix="tpe_vision_"))
        try:
            text = docx2txt.process(str(path), str(img_dir))
            docs = [Document(page_content=text, metadata={"source": path.name, "page": 0})]
            
            vision_descriptions = process_document_images(img_dir)
            for desc in vision_descriptions:
                docs.append(Document(page_content=desc, metadata={"source": path.name, "page": 0, "is_image": True}))
                
            return docs
        finally:
            shutil.rmtree(img_dir, ignore_errors=True)
    return []

def ingest_document(path: Path) -> dict:
    """
    Ingère un document de manière incrémentale.
    """
    file_hash = calculate_hash(path)
    
    if check_hash_exists(file_hash):
        return {"status": "ignored", "chunks": 0, "hash": file_hash}
        
    documents = load_document(path)
    if not documents:
        return {"status": "error", "chunks": 0, "hash": file_hash}
    
    # Nettoyage
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    
    filename_meta = extract_metadata_from_filename(path.name)

    for i, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "source": path.name,
                "document_type": "pdf",
                "file_hash": file_hash,
                "platform": filename_meta["platform"],
                "version": filename_meta["version"],
                "chunk_index": i,
                # PyPDFLoader ajoute déjà 'page'
            }
        )

    get_vector_store().add_documents(chunks)
    return {"status": "ingested", "chunks": len(chunks), "hash": file_hash}


def ingest_all() -> dict[str, dict]:
    documents_dir = Path(settings.documents_dir)
    documents_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    for path in documents_dir.glob("*"):
        if path.suffix.lower() in [".pdf", ".docx"]:
            result[path.name] = ingest_document(path)

    return result
