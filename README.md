# ENT AI Assistant

Assistant IA destiné à aider les utilisateurs à comprendre facilement les applications de l'ENT.

## Architecture du MVP

- FastAPI : API du microservice IA
- Agent Core : orchestration métier
- LangChain : RAG et orchestration LLM
- LM Studio : LLM local via endpoint OpenAI-compatible
- ChromaDB : base vectorielle locale
- PyPDF : extraction des PDF
- MockEntApiClient : abstraction de l'API ENT pour le développement

Le microservice IA ne communique jamais directement avec PostgreSQL.

## Démarrage

1. Démarrer le serveur local dans LM Studio et charger un modèle.
2. Copier `.env.example` vers `.env` et renseigner `LM_MODEL`.
3. Installer : `pip install -r requirements.txt`
4. Déposer les PDF dans `data/documents/`
5. Indexer : `python -m app.scripts.ingest`
6. Lancer l'API : `uvicorn app.main:app --reload`

Tester `POST /api/v1/chat` avec :

```json
{"message": "Comment créer un utilisateur ?"}
```

## Étapes suivantes

1. Ajouter les citations de sources/page dans les réponses.
2. Ajouter le contexte utilisateur.
3. Brancher `HttpEntApiClient` sur Django/DRF.
4. Ajouter les outils ENT nécessaires.
5. Ajouter Gemini comme second provider.
6. Ajouter l'authentification/Keycloak au niveau de l'ENT.
