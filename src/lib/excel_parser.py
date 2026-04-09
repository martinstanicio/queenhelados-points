import io

import pandas as pd


class ExcelParser:
    def parse(self, byte_stream: io.BytesIO) -> pd.DataFrame:
        try:
            return pd.read_excel(byte_stream)
        except Exception as parsing_error:
            raise ValueError(
                f"Error crítico al parsear el flujo de bytes de Excel: {parsing_error}"
            )
