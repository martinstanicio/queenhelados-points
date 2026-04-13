import io
from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    @abstractmethod
    def list_files(self) -> list[str]:
        pass

    @abstractmethod
    def open_file(self, path: str) -> io.BytesIO:
        pass
