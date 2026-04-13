import io
from abc import ABC, abstractmethod

import pandas as pd


class FileParser(ABC):
    @abstractmethod
    def parse(self, byte_stream: io.BytesIO) -> pd.DataFrame:
        pass
