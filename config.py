from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    football_data_api_key: str = ""
    odds_api_key: str = ""
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///db/sqlite.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()