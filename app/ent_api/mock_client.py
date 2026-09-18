from app.ent_api.base import EntApiClient


class MockEntApiClient(EntApiClient):
    def get_current_user(self) -> dict:
        return {
            "id": "demo-user-001",
            "name": "Utilisateur Démo",
            "email": "demo@example.com",
        }

    def list_platforms(self, user_id: str) -> list[str]:
        # On simule un filtrage : tous les utilisateurs ont accès à ces 3 apps
        return ["Produits", "Ventes", "Messagerie"]
