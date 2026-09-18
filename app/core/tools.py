from langchain_core.tools import tool
from app.ent_api.mock_client import MockEntApiClient

# Dans une application réelle, on utiliserait une injection de dépendance 
# ou on choisirait entre MockEntApiClient et HttpEntApiClient en fonction de la config.
ent_api = MockEntApiClient()

@tool
def get_user_info_tool() -> str:
    """
    Retourne les informations de l'utilisateur actuellement connecté.
    Outil très utile pour connaître l'identifiant (id) ou le nom de l'utilisateur avant de lister ses accès.
    """
    user = ent_api.get_current_user()
    return f"L'utilisateur connecté s'appelle {user['name']} (ID: {user['id']}, Email: {user['email']})."

@tool
def list_accessible_platforms_tool(user_id: str) -> str:
    """
    Retourne la liste des plateformes/applications de l'ENT auxquelles un utilisateur a accès.
    Nécessite l'ID de l'utilisateur.
    """
    platforms = ent_api.list_platforms(user_id)
    if not platforms:
        return "Cet utilisateur n'a accès à aucune plateforme."
    return f"L'utilisateur {user_id} a accès aux plateformes suivantes : {', '.join(platforms)}."

