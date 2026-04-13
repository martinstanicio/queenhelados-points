import pandas as pd

from data_processors.data_processor import DataProcessor


class ClientListProcessor(DataProcessor):
    def __init__(self) -> None:
        self.skipped_header_rows = 2
        self.skipped_footer_rows = 0
        self.columns = {
            "client_number": int,
            "client_name": str,
            "client_address": str,
            "client_city": str,
            "client_cuit": str,
            "client_phones": str,
            "client_email": str,
        }
        self.email_regex = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            new_df = self._skipped_rows(df, header_rows=2, footer_rows=0)
            new_df = self._mapped_columns(new_df, column_mapping=self.columns)

            new_df = new_df.dropna(
                subset=["client_number", "client_name", "client_email"]
            )

            new_df["client_email"] = new_df["client_email"].str.strip().str.lower()
            valid_email_mask = new_df["client_email"].str.match(
                self.email_regex, na=False
            )
            new_df = new_df[valid_email_mask]

            return new_df[["client_number", "client_name", "client_email"]]

        except Exception as e:
            raise ValueError(f"Error processing ClientList file: {e}")
