from abc import ABC, abstractmethod

from pandas import DataFrame


class APICaller(ABC):
    @abstractmethod
    def call(self, df: DataFrame) -> set[str]:
        pass
