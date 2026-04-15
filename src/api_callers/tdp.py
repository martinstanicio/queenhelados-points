import pandas as pd
import requests

from api_callers.api_caller import APICaller


class TiendaDePuntosCaller(APICaller):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api.tiendadepuntos.com"
        self.endpoint = f"{self.base_url}/external/tags/add"
        self.headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

    def call(self, df: pd.DataFrame) -> set[str]:
        processed_document_ids = set()

        for _, row in df.iterrows():
            document_id = row["document_id"]
            payload = {
                "amount": row["total_price"],
                "ignoreCreateClient": False,
                "client": {"email": row["client_email"]},
                "reason": document_id,
            }

            try:
                response = requests.post(
                    self.endpoint, json=payload, headers=self.headers
                )

                if response.status_code == 201:
                    processed_document_ids.add(document_id)
                else:
                    print(
                        f"[!] API Error {response.status_code} for {document_id}: {response.text}"
                    )

            except Exception as e:
                print(f"[❌] Network error for {document_id}: {e}")

        return processed_document_ids
