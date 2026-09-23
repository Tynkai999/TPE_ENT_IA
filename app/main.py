from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.rag.ingestion import ingest_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hook de démarrage/arrêt de l'application FastAPI.
    Au démarrage : ingère automatiquement les nouveaux documents.
    """
    # --- Startup ---
    print("[Auto-Ingest] Vérification des nouveaux documents...")
    result = ingest_all()
    if result:
        new_count = sum(1 for d in result.values() if d.get("status") == "ingested")
        if new_count > 0:
            print(f"[Auto-Ingest] {new_count} nouveau(x) document(s) ingéré(s). ✅")
        else:
            print("[Auto-Ingest] Tous les documents sont déjà à jour. ✅")
    
    yield  # L'application tourne ici
    
    # --- Shutdown ---
    print("[Shutdown] Arrêt de l'application.")


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Assistant IA pour aider les utilisateurs à comprendre les applications de l'ENT.",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}
