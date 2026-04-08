from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:tarikgg13@localhost:5432/my_trello"
    SECRET_KEY: str = "dielit"

settings = Settings()