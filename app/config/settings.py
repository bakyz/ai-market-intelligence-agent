from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# =========================
# Model Configuration
# =========================
class ModelConfig(BaseSettings):
    CHAT_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1000


class ModelRoutingConfig(BaseSettings):
    IDEATION_MODEL: str = "gpt-4o-mini"
    ANALYSIS_MODEL: str = "gpt-4o"
    SUMMARIZATION_MODEL: str = "gpt-4o-mini"


# =========================
# Vector Database Config
# =========================
class VectorDBConfig(BaseSettings):
    PROVIDER: Literal["chroma", "pinecone", "qdrant"] = "chroma"
    COLLECTION_NAME: str = "documents"
    PERSIST_DIR: str = "./vector_store"


# =========================
# Logging + Observability
# =========================
class LoggingConfig(BaseSettings):
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FILE: str = "./logs/app.log"


class ObservabilityConfig(BaseSettings):
    ENABLE_TRACING: bool = True
    TRACE_LLM_CALLS: bool = True
    TRACE_PIPELINES: bool = True


# =========================
# Scraper Config
# =========================
class ScraperConfig(BaseSettings):
    REDDIT_LIMIT: int = 100
    HN_LIMIT: int = 100
    X_LIMIT: int = 100
    REQUEST_TIMEOUT: int = 10
    RETRIES: int = 3
    RATE_LIMIT_PER_MINUTE: int = 30
    BACKOFF_FACTOR: float = 1.5


# =========================
# LLM Control
# =========================
class LLMConfig(BaseSettings):
    MAX_RETRIES: int = 3
    TIMEOUT: int = 60
    COST_LIMIT_PER_RUN: float = 5.0


# =========================
# Pipeline Config
# =========================
class PipelineConfig(BaseSettings):
    BATCH_SIZE: int = 32
    EMBEDDING_BATCH_SIZE: int = 64
    ENABLE_PARALLEL_STAGES: bool = True


# =========================
# Runtime Flags
# =========================
class RuntimeFlags(BaseSettings):
    ENABLE_LLM: bool = True
    ENABLE_SCRAPING: bool = True
    DRY_RUN: bool = False


# =========================
# Cache Config
# =========================
class CacheConfig(BaseSettings):
    ENABLE_CACHE: bool = True
    CACHE_DIR: str = "./cache"


# =========================
# Worker / Async Config
# =========================
class WorkerConfig(BaseSettings):
    MAX_CONCURRENT_TASKS: int = 5
    QUEUE_SIZE: int = 100


# =========================
# Paths Config
# =========================
class Paths(BaseSettings):
    RAW_DATA: str = "data/raw"
    PROCESSED_DATA: str = "data/processed"
    REPORTS: str = "reports"


# =========================
# Root Application Settings
# =========================
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    OPENAI_API_KEY: str
    PINECONE_API_KEY: str | None = None
    ENV: Literal["development", "staging", "production"] = "development"

    model: ModelConfig = ModelConfig()
    model_routing: ModelRoutingConfig = ModelRoutingConfig()
    vectordb: VectorDBConfig = VectorDBConfig()

    logging: LoggingConfig = LoggingConfig()
    observability: ObservabilityConfig = ObservabilityConfig()

    scraper: ScraperConfig = ScraperConfig()
    llm: LLMConfig = LLMConfig()
    pipeline: PipelineConfig = PipelineConfig()

    runtime_flags: RuntimeFlags = RuntimeFlags()
    cache: CacheConfig = CacheConfig()
    worker: WorkerConfig = WorkerConfig()
    paths: Paths = Paths()


# =========================
# Settings Factory (Singleton)
# =========================
@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


# default instance
settings = get_settings()
