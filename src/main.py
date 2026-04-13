import os

from dotenv import load_dotenv

from file_parsers.excel import ExcelParser
from lib.orchestrator import Orchestrator
from storage_adapters.gdrive import GoogleDriveAdapter


def main() -> None:
    load_dotenv()

    FOLDER_ID = os.environ.get("FOLDER_ID")
    TARGET_SERVICE_ACCOUNT = os.environ.get("TARGET_SERVICE_ACCOUNT")

    if not FOLDER_ID or not TARGET_SERVICE_ACCOUNT:
        raise ValueError(
            "Environment variables FOLDER_ID and TARGET_SERVICE_ACCOUNT must be set."
        )

    storage = GoogleDriveAdapter(FOLDER_ID, TARGET_SERVICE_ACCOUNT)
    parser = ExcelParser()
    orchestrator = Orchestrator(storage, parser)

    df = orchestrator.get_denormalized_data()



if __name__ == "__main__":
    main()
