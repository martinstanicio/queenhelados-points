import pandas as pd

from data_processors.client_list import ClientListProcessor
from data_processors.pos import POSProcessor
from data_processors.sales_by_article import SalesByArticleProcessor
from file_parsers.file_parser import FileParser
from storage_adapters.storage_adapter import StorageAdapter
from util.path import get_path_components


class Orchestrator:
    def __init__(self, storage: StorageAdapter, parser: FileParser) -> None:
        self.storage = storage
        self.parser = parser
        self.sales_by_article_processor = SalesByArticleProcessor()
        self.client_list_processor = ClientListProcessor()
        self.pos_processor = POSProcessor()

    def get_denormalized_data(self) -> pd.DataFrame:
        df_pos = self.pos_processor.process(
            self.parser.parse(self.storage.open_file("puntos-de-venta.xlsx"))
        )

        all_files = self.storage.list_files()
        list_sales_dfs: list[pd.DataFrame] = []
        list_client_dfs: list[pd.DataFrame] = []

        for file_path in all_files:
            path_components = get_path_components(file_path)

            if len(path_components) < 2:
                continue

            subfolder = path_components[0]
            try:
                match subfolder:
                    case "ventas-por-articulo":
                        df_raw = self.parser.parse(self.storage.open_file(file_path))
                        list_sales_dfs.append(
                            self.sales_by_article_processor.process(df_raw)
                        )

                    case "listado-de-clientes":
                        file_name = path_components[1]
                        branch_id = file_name.split(".")[0]
                        df_raw = self.parser.parse(self.storage.open_file(file_path))
                        df_clients = self.client_list_processor.process(df_raw)
                        df_clients["branch_id"] = branch_id
                        list_client_dfs.append(df_clients)
            except Exception as e:
                print(f"[!] Error processing {file_path}: {e}")

        if not list_sales_dfs or not list_client_dfs:
            return pd.DataFrame()

        df_sales = pd.concat(list_sales_dfs, ignore_index=True)
        df_clients = pd.concat(list_client_dfs, ignore_index=True)

        df_sales_pos = pd.merge(df_sales, df_pos, on="pos_id", how="left")
        df_sales_pos_clients = pd.merge(
            df_sales_pos, df_clients, on=["client_number", "branch_id"], how="left"
        )
        df_sales_pos_clients["document_id"] = (
            df_sales_pos_clients["document_type"].str.strip()
            + df_sales_pos_clients["tax_condition"].str.strip()
            + df_sales_pos_clients["pos_id"].str.zfill(5)
            + "-"
            + df_sales_pos_clients["document_number"].str.zfill(8)
        )

        df = (
            df_sales_pos_clients.groupby("document_id")
            .agg(
                {
                    "date": "first",
                    "time": "first",
                    "branch_id": "first",
                    "client_number": "first",
                    "client_email": "first",
                    "total_price": "sum",
                }
            )
            .reset_index()
        )

        return df
