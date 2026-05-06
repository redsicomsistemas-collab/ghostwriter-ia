from dataclasses import dataclass
import json
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.2")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ghostwriter.db")
    buffer_access_token: str = os.getenv("BUFFER_ACCESS_TOKEN", "")
    buffer_profile_ids_raw: str = os.getenv("BUFFER_PROFILE_IDS", "{}")
    default_brand_context: str = os.getenv(
        "DEFAULT_BRAND_CONTEXT",
        "Escribe en primera persona, con criterio practico y sin sonar corporativo.",
    )

    @property
    def buffer_profile_ids(self) -> dict[str, str]:
        parsed = json.loads(self.buffer_profile_ids_raw)
        if not isinstance(parsed, dict):
            raise ValueError("BUFFER_PROFILE_IDS debe ser un objeto JSON")
        return {str(key).lower(): str(value) for key, value in parsed.items()}


settings = Settings()
