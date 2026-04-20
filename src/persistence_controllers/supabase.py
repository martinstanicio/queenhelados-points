from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from persistence_controllers.persistence_controller import PersistenceController


class SupabaseController(PersistenceController):
    def __init__(self, url: str, service_role_key: str) -> None:
        self.client: Client = create_client(
            url,
            service_role_key,
            options=SyncClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
        self.table_name = "processed_documents"
        self.column_name = "id"

    def get_processed_document_ids(self) -> set[str]:
        response = self.client.table(self.table_name).select(self.column_name).execute()
        processed_ids: set[str] = set()

        for row in response.data:
            processed_ids.add(row[self.column_name])

        return processed_ids

    def add_processed_document_ids(self, document_ids: list[str]) -> None:
        if not document_ids:
            return

        data = [{"id": id} for id in document_ids]

        self.client.table(self.table_name).upsert(data).execute()
