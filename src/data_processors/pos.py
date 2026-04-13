import pandas as pd

from data_processors.data_processor import DataProcessor


class POSProcessor(DataProcessor):
    def __init__(self) -> None:
        self.column_mapping = {
            "pos_id": int,
            "branch_id": str,
        }

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            processed_df = self._mapped_columns(df, column_mapping=self.column_mapping)

            return processed_df[["pos_id", "branch_id"]]
        except Exception as e:
            raise ValueError(f"Error processing POS file: {e}")
