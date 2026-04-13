import pandas as pd

from file_processors.file_processor import FileProcessor


class SalesByArticleProcessor(FileProcessor):
    def __init__(self) -> None:
        self.vat_multiplier = 1.21
        self.skipped_header_rows = 4
        self.skipped_footer_rows = 2
        self.columns = {
            "date": str,
            "time": str,
            "article_code": int,
            "article_name": str,
            "quantity": int,
            "unit_price": float,
            "total_price": float,
            "document_type": str,
            "tax_condition": str,
            "pos_id": int,
            "_": str,
            "document_number": int,
            "client_number": int,
            "client_name": str,
        }

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            new_df = df.iloc[
                self.skipped_header_rows : len(df) - self.skipped_footer_rows
            ].copy()
            new_df.columns = list(self.columns.keys())
            new_df = new_df.astype(self.columns)
            new_df = new_df.drop(columns=["_"])

            mask_b = new_df["tax_condition"] == "B"
            new_df.loc[mask_b, "unit_price"] = (
                new_df.loc[mask_b, "unit_price"] * self.vat_multiplier
            ).round(2)

            new_df["total_price"] = (new_df["unit_price"] * new_df["quantity"]).round(2)

            return new_df

        except Exception as e:
            raise ValueError(f"Error processing SalesByArticle file: {e}")
