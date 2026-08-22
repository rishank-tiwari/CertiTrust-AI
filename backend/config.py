from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRY_HOURS: int
    UPLOAD_DIR: str
    MAX_FILE_SIZE_MB: int
    ALLOWED_ORIGINS: str = ""

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
