import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # LLM (Gemini Developer API — get a key at https://aistudio.google.com/apikey)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")

    # Storage
    db_path: str = os.getenv("DB_PATH", "data/mace.db")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "data/faiss_index")

    # Orchestrator
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
    max_orchestration_cycles: int = int(os.getenv("MAX_ORCHESTRATION_CYCLES", "10"))

    # Auth
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"


settings = Settings()
