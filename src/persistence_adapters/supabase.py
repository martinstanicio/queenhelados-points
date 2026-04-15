from typing import Any, Mapping

from supabase import Client, create_client

from persistence_adapters.persistence_adapter import PersistenceAdapter


class SupabaseAdapter(PersistenceAdapter):
    def __init__(self, url: str, api_key: str) -> None:
        self.client: Client = create_client(url, api_key)
        self.table_name = "processed_documents"

    def get_processed_document_ids(self) -> set[str]:
        response = self.client.table(self.table_name).select("document_id").execute()
        processed_ids: set[str] = set()

        for row in response.data:
            if row is not Mapping[str, Any]:
                continue

            processed_ids.add(row["document_id"])

        return processed_ids

    def add_processed_document_ids(self, document_ids: list[str]) -> None:
        if not document_ids:
            return

        data = [{"document_id": id} for id in document_ids]

        # Batch insert is more efficient than individual calls
        self.client.table(self.table_name).insert(data).execute()
