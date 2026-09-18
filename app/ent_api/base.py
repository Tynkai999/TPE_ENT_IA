from abc import ABC, abstractmethod


class EntApiClient(ABC):
    # Contrat entre l'agent IA et l'API ENT.
    # Aucun accès direct à PostgreSQL.

    @abstractmethod
    def get_current_user(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_platforms(self, user_id: str) -> list[str]:
        raise NotImplementedError
