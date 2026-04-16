from api_callers.api_caller import APICaller
from api_callers.tdp import TiendaDePuntosCaller
from file_parsers.excel import ExcelParser
from file_parsers.file_parser import FileParser
from lib.config import Config
from lib.orchestrator import Orchestrator
from persistence_adapters.persistence_adapter import PersistenceAdapter
from persistence_adapters.supabase import SupabaseAdapter
from storage_adapters.gdrive import GoogleDriveAdapter
from storage_adapters.storage_adapter import StorageAdapter


def main() -> None:
    # IGNORED_CLIENT_NUMBERS = Config.get_optional(
    #     "IGNORED_CLIENT_NUMBERS", default="1, 4, 7, 9, 10, 11, 13, 14, 15, 17"
    # )

    # if IGNORED_CLIENT_NUMBERS:
    #     IGNORED_CLIENT_NUMBERS = list(map(int, IGNORED_CLIENT_NUMBERS.split(",")))

    IGNORED_CLIENT_NUMBERS = [i for i in range(1, 9999 + 1) if i != 4048]

    storage: StorageAdapter = GoogleDriveAdapter(
        Config.get_required("GDRIVE_FOLDER_ID"),
        Config.get_required("GDRIVE_TARGET_SERVICE_ACCOUNT"),
    )
    parser: FileParser = ExcelParser()
    orchestrator = Orchestrator(
        storage, parser, Config.get_optional("START_DATE"), IGNORED_CLIENT_NUMBERS
    )
    api_caller: APICaller = TiendaDePuntosCaller(Config.get_required("TDP_API_KEY"))
    persistence_adapter: PersistenceAdapter = SupabaseAdapter(
        Config.get_required("SUPABASE_URL"),
        Config.get_required("SUPABASE_SECRET_KEY"),
    )

    df = orchestrator.get_denormalized_data()

    if df.empty:
        return

    existing_processed_ids = persistence_adapter.get_processed_document_ids()

    # Using ~ and isin for an efficient boolean mask filtering
    df_filtered = df[~df["document_id"].isin(existing_processed_ids)].copy()

    if df_filtered.empty:
        return

    newly_processed_ids = api_caller.call(df_filtered)

    if newly_processed_ids:
        persistence_adapter.add_processed_document_ids(list(newly_processed_ids))


if __name__ == "__main__":
    main()
