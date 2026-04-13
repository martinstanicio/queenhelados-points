from abc import ABC, abstractmethod

import pandas as pd


class DataProcessor(ABC):
    @abstractmethod
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    def _skipped_rows(
        self, df: pd.DataFrame, header_rows: int, footer_rows: int
    ) -> pd.DataFrame:
        return df.iloc[header_rows : len(df) - footer_rows].copy()

    def _mapped_columns(self, df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        df.columns = list(column_mapping.keys())
        return df.astype(column_mapping)
