import io

import google.auth
from google.auth import impersonated_credentials as get_impersonated_credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from adapters.storage_adapter import StorageAdapter
from util.path import get_path_components

ONE_HOUR_IN_SECONDS = 60 * 60


class GoogleDriveAdapter(StorageAdapter):
    def __init__(
        self,
        folder_id: str,
        target_service_account: str,
        lifetime_seconds: int = ONE_HOUR_IN_SECONDS,
    ) -> None:
        self.folder_id = folder_id
        self.target_service_account = target_service_account
        self.lifetime_seconds = lifetime_seconds
        self.scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        self.service = self._authenticate()

    def _authenticate(self):  # noqa: ANN202
        try:
            credentials, _ = google.auth.default()
            impersonated_credentials = get_impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=self.target_service_account,
                lifetime=self.lifetime_seconds,
                target_scopes=self.scopes,
            )
            return build("drive", "v3", credentials=impersonated_credentials)
        except Exception as authentication_error:
            raise ValueError(
                f"Critical error authenticating with Google Drive via ADC: {authentication_error}"
            )

    def _download_file(self, file_id: str) -> io.BytesIO:
        try:
            download_request = self.service.files().get_media(fileId=file_id)
            file_byte_stream = io.BytesIO()
            media_downloader = MediaIoBaseDownload(file_byte_stream, download_request)

            is_download_complete: bool = False
            while not is_download_complete:
                _, is_download_complete = media_downloader.next_chunk()

            # Resetting the stream pointer to 0 ensures the downstream parser
            # (e.g., pandas/xlrd) reads the file data from the very beginning.
            file_byte_stream.seek(0)
            return file_byte_stream

        except Exception as download_error:
            raise RuntimeError(f"Error downloading file {file_id}: {download_error}")

    def list_files(self) -> list[str]:
        matched_relative_paths: list[str] = []
        pending_folders_stack: list[tuple[str, str]] = [(self.folder_id, "")]

        while pending_folders_stack:
            current_folder_id, current_relative_path = pending_folders_stack.pop()
            drive_api_query = f"'{current_folder_id}' in parents and trashed=false"

            try:
                next_page_token: str | None = None

                while True:
                    api_response = (
                        self.service.files()
                        .list(
                            q=drive_api_query,
                            fields="nextPageToken, files(id, name, mimeType)",
                            pageToken=next_page_token,
                        )
                        .execute()
                    )

                    drive_items = api_response.get("files", [])

                    for item in drive_items:
                        item_name: str = item["name"]
                        item_relative_path: str = (
                            item_name
                            if current_relative_path == ""
                            else f"{current_relative_path}/{item_name}"
                        )

                        if item["mimeType"] == "application/vnd.google-apps.folder":
                            pending_folders_stack.append(
                                (item["id"], item_relative_path)
                            )
                        else:
                            matched_relative_paths.append(item_relative_path)

                    next_page_token: str | None = api_response.get("nextPageToken")
                    if not next_page_token:
                        break

            except Exception as traversal_error:
                raise RuntimeError(
                    f"Error traversing Drive folder {current_folder_id}: {traversal_error}"
                )

        return matched_relative_paths

    def open_file(self, path: str) -> io.BytesIO:
        path_components = get_path_components(path)
        current_node_id = self.folder_id

        for index, node_name in enumerate(path_components):
            drive_api_query = f"'{current_node_id}' in parents and name='{node_name}' and trashed=false"

            try:
                api_response: dict = (
                    self.service.files()
                    .list(q=drive_api_query, fields="files(id, mimeType)")
                    .execute()
                )

                matching_items: list[dict] = api_response.get("files", [])
                if not matching_items:
                    raise FileNotFoundError(
                        f"Path component '{node_name}' not found in Drive."
                    )

                # Google Drive allows duplicate names in the same directory.
                # Assuming the first match is the intended target.
                target_item = matching_items[0]
                current_node_id = target_item["id"]

                is_last_component = index == len(path_components) - 1
                is_folder_node = (
                    target_item["mimeType"] == "application/vnd.google-apps.folder"
                )

                if not is_last_component and not is_folder_node:
                    raise NotADirectoryError(
                        f"'{node_name}' is a file, but a folder was expected."
                    )
                if is_last_component and is_folder_node:
                    raise IsADirectoryError(
                        f"'{node_name}' is a folder, but a file was expected."
                    )

            except Exception as resolution_error:
                if isinstance(
                    resolution_error,
                    (FileNotFoundError, NotADirectoryError, IsADirectoryError),
                ):
                    raise resolution_error
                raise RuntimeError(
                    f"Error resolving path component '{node_name}': {resolution_error}"
                )

        return self._download_file(current_node_id)
