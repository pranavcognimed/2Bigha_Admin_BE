# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAIL_FROM: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    SQLALCHEMY_DATABASE_URL: str
    MAIL_SERVER: str
    MAIL_PORT: int

    class Config:
        env_file = ".env"

settings = Settings()
