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
    auto_mode_enabled: bool = os.getenv("AUTO_MODE_ENABLED", "false").lower() == "true"
    auto_publish_enabled: bool = os.getenv("AUTO_PUBLISH_ENABLED", "false").lower() == "true"
    auto_content_feed_url: str = os.getenv("AUTO_CONTENT_FEED_URL", "")
    auto_content_topics_raw: str = os.getenv("AUTO_CONTENT_TOPICS", "")
    auto_content_platforms_raw: str = os.getenv("AUTO_CONTENT_PLATFORMS", "linkedin,x,instagram")
    auto_post_interval_minutes: int = int(os.getenv("AUTO_POST_INTERVAL_MINUTES", "480"))
    auto_post_limit_per_run: int = int(os.getenv("AUTO_POST_LIMIT_PER_RUN", "1"))

    @property
    def buffer_profile_ids(self) -> dict[str, str]:
        parsed = json.loads(self.buffer_profile_ids_raw)
        if not isinstance(parsed, dict):
            raise ValueError("BUFFER_PROFILE_IDS debe ser un objeto JSON")
        return {str(key).lower(): str(value) for key, value in parsed.items()}

    @property
    def auto_content_topics(self) -> list[str]:
        return [topic.strip() for topic in self.auto_content_topics_raw.split("|") if topic.strip()]

    @property
    def auto_content_platforms(self) -> list[str]:
        return [platform.strip().lower() for platform in self.auto_content_platforms_raw.split(",") if platform.strip()]


settings = Settings()
