from abc import ABC, abstractmethod


class PersistenceAdapter(ABC):
    @abstractmethod
    def get_processed_document_ids(self) -> set[str]:
        pass

    @abstractmethod
    def add_processed_document_ids(self, document_ids: list[str]) -> None:
        pass
