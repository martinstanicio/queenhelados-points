import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    @staticmethod
    def get_required(key: str) -> str:
        value = os.environ.get(key)

        if not value:
            raise ValueError(f"Environment variable '{key}' is missing or empty.")

        return value

    @staticmethod
    def get_optional(key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)
