import pandas as pd

from data_processors.articles import ArticlesProcessor
from data_processors.client_list import ClientListProcessor
from data_processors.pos import POSProcessor
from data_processors.sales_by_article import SalesByArticleProcessor
from file_parsers.file_parser import FileParser
from storage_adapters.storage_adapter import StorageAdapter
from util.path import get_path_components


class Orchestrator:
    def __init__(
        self,
        storage: StorageAdapter,
        parser: FileParser,
        start_date: str | None,  # YYYYMMDD
        ignored_client_numbers: list[int] | None,
    ) -> None:
        self.storage = storage
        self.parser = parser
        self.sales_by_article_processor = SalesByArticleProcessor()
        self.client_list_processor = ClientListProcessor()
        self.pos_processor = POSProcessor()
        self.articles_processor = ArticlesProcessor()
        self.start_date = start_date or "00000000"
        self.ignored_client_numbers = ignored_client_numbers or list()

    def get_denormalized_data(self) -> pd.DataFrame:
        df_pos = self.pos_processor.process(
            self.parser.parse(self.storage.open_file("puntos-de-venta.xlsx"))
        )
        df_articles = self.articles_processor.process(
            self.parser.parse(self.storage.open_file("productos.xlsx"))
        )

        all_files = self.storage.list_files()
        list_sales_dfs: list[pd.DataFrame] = []
        list_client_dfs: list[pd.DataFrame] = []

        for file_path in all_files:
            path_components = get_path_components(file_path)

            if len(path_components) < 2:
                continue

            subfolder = path_components[0]
            file_name = path_components[1]
            file_date = file_name.split("-")[0]

            if file_date < self.start_date:
                continue

            try:
                match subfolder:
                    case "ventas-por-articulo":
                        df_raw = self.parser.parse(self.storage.open_file(file_path))
                        df_sales = self.sales_by_article_processor.process(df_raw)
                        df_sales = df_sales[
                            ~df_sales["client_number"].isin(self.ignored_client_numbers)
                        ]
                        list_sales_dfs.append(df_sales)
                    case "listado-de-clientes":
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

        df_sales_articles = pd.merge(
            df_sales,
            df_articles,
            on="article_code",
            how="left",
        )
        df_sales_articles["points_multiplier"] = df_sales_articles[
            "points_multiplier"
        ].fillna(1.0)

        df_sales_articles["total_price"] = (
            df_sales_articles["total_price"] * df_sales_articles["points_multiplier"]
        )

        df_sales_articles_pos = pd.merge(
            df_sales_articles, df_pos, on="pos_id", how="inner"
        )
        df_sales_articles_pos_clients = pd.merge(
            df_sales_articles_pos,
            df_clients,
            on=["client_number", "branch_id"],
            how="inner",
        )

        df_sales_articles_pos_clients["document_id"] = (
            df_sales_articles_pos_clients["document_type"].str.strip()
            + df_sales_articles_pos_clients["tax_condition"].str.strip()
            + df_sales_articles_pos_clients["pos_id"].astype(str).str.zfill(5)
            + "-"
            + df_sales_articles_pos_clients["document_number"].astype(str).str.zfill(8)
        )

        df = (
            df_sales_articles_pos_clients.groupby("document_id")
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
