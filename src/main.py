from api_callers.api_caller import APICaller
from api_callers.tdp import TiendaDePuntosCaller
from file_parsers.excel import ExcelParser
from file_parsers.file_parser import FileParser
from lib.config import Config
from lib.orchestrator import Orchestrator
from persistence_controllers.persistence_controller import PersistenceController
from persistence_controllers.supabase import SupabaseController
from storage_adapters.gdrive import GoogleDriveAdapter
from storage_adapters.storage_adapter import StorageAdapter


def main() -> None:
    _IGNORED_CLIENT_NUMBERS = Config.get_optional(
        "IGNORED_CLIENT_NUMBERS", default="1, 4, 7, 9, 10, 11, 13, 14, 15, 17"
    )

    try:
        IGNORED_CLIENT_NUMBERS = (
            list(map(int, _IGNORED_CLIENT_NUMBERS.split(",")))
            if _IGNORED_CLIENT_NUMBERS
            else None
        )
    except ValueError:
        pass

    storage: StorageAdapter = GoogleDriveAdapter(
        Config.get_required("GDRIVE_FOLDER_ID"),
        Config.get_required("GDRIVE_TARGET_SERVICE_ACCOUNT"),
    )
    parser: FileParser = ExcelParser()
    orchestrator = Orchestrator(
        storage,
        parser,
        Config.get_optional("START_DATE"),
        IGNORED_CLIENT_NUMBERS,
    )
    api_caller: APICaller = TiendaDePuntosCaller(Config.get_required("TDP_API_KEY"))
    persistence_controller: PersistenceController = SupabaseController(
        Config.get_required("SUPABASE_URL"),
        Config.get_required("SUPABASE_SECRET_KEY"),
    )

    df = orchestrator.get_denormalized_data()

    ALLOWED_BRANCH_ID = "escobar"
    ALLOWED_CLIENT_NUMBERS = [
        37,
        40,
        43,
        60,
        62,
        61,
        63,
        69,
        70,
        453,
        1307,
        2365,
        2594,
        2627,
        3391,
        3394,
        3402,
        4048,
    ]

    df = df[
        (df["branch_id"] == ALLOWED_BRANCH_ID)
        & (df["client_number"].isin(ALLOWED_CLIENT_NUMBERS))
    ].copy()

    if df.empty:
        return

    existing_processed_ids = persistence_controller.get_processed_document_ids()

    # Using ~ and isin for an efficient boolean mask filtering
    df_filtered = df[~df["document_id"].isin(existing_processed_ids)].copy()

    if df_filtered.empty:
        return

    newly_processed_ids = api_caller.call(df_filtered)

    if newly_processed_ids:
        persistence_controller.add_processed_document_ids(list(newly_processed_ids))


if __name__ == "__main__":
    main()
