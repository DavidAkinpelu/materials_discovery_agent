from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    EXA_API_KEY: Optional[str] = None
    MP_API_KEY: Optional[str] = None
    
    # Langfuse Observability (Optional)
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    ENABLE_LANGFUSE: bool = False
    
    # Application Settings
    LOG_LEVEL: str = "INFO"
    HTTP_TIMEOUT: float = 30.0
    
    # Model Configuration
    MODEL_NAME: str = "gpt-4o"
    MODEL_TEMPERATURE: float = 0.0
    
    # Agent Configuration
    MAX_HISTORY_TURNS: int = 5  # Number of past conversation turns to include in context
    MAX_AGENT_ITERATIONS: int = 10 # Max iterations for ReAct agent
    MAX_REFINEMENT_LOOPS: int = 3  # Maximum number of validation/refinement cycles
    MAX_LOG_LENGTH: int = 500 # Truncation length for logs/reasoning traces
    
    # Search Settings
    DEFAULT_SEARCH_RESULTS: int = 5
    MP_SEARCH_LIMIT: int = 20
    SURECHEMBL_PAGE_SIZE: int = 10
    
    # Caching (Seconds)
    CACHE_TTL_HOURS: int = 24 # Generic fallback
    CACHE_MAX_SIZE: int = 1000
    
    CACHE_TTL_SEARCH_SHORT: int = 86400       # 24 hours (e.g. prices)
    CACHE_TTL_SEARCH_LONG: int = 604800       # 7 days (e.g. concepts)
    CACHE_TTL_MP_DATA: int = 604800           # 7 days
    CACHE_TTL_MP_STATS: int = 2592000         # 30 days
    CACHE_TTL_PATENTS: int = 86400            # 24 hours
    CACHE_TTL_STRUCTURES: int = 604800        # 7 days

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars

settings = Settings()
