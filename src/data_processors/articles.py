import pandas as pd

from data_processors.data_processor import DataProcessor


class ArticlesProcessor(DataProcessor):
    def __init__(self) -> None:
        self.column_mapping = {
            "article_code": int,
            "article_name": str,
            "presentation": str,
            "category": str,
            "brand": str,
            "points_multiplier": float,
        }

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            processed_df = self._mapped_columns(df, column_mapping=self.column_mapping)

            return processed_df[
                [
                    "article_code",
                    "article_name",
                    "presentation",
                    "category",
                    "brand",
                    "points_multiplier",
                ]
            ]
        except Exception as e:
            raise ValueError(f"Error processing Articles file: {e}")
