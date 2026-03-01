from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = "devsecret"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env.dev"

settings = Settings()