from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "./storage/chroma"
    max_upload_mb: int = 25

    class Config:
        env_file = ".env"


settings = Settings()
