from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    # env
    DEBUG: bool

    HOST: str
    PORT: int

    DB_PATH: str

    REDIS_URL: str
    REDIS_EXPIRE: int
    REDIS_POOL_SIZE: int
    REDIS_PREFIX: str

    BLOCKER_URL: str
    BLOCKER_REDIS_PREFIX: str
    BLOCKER_ACCESS_CODE: str

    FRONTEND_URL: str


settings = Settings()
