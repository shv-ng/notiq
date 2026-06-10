from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "postgres"

    redis_url: str = "redis://redis:6379/0"

    secret_key: str = "abc123"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
