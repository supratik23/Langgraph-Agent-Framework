from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application Settings. These settings will be loaded from environment variables or a .env file. 
    In the server it will be loaded from environment variables, and in development it will be loaded from a .env file.
    """

    OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_MODEL: str

    AZURE_SEARCH_SERVICE_NAME: str
    AZURE_SEARCH_API_KEY: str
    AZURE_SEARCH_SEMANTIC_CONFIGURATION: str | None = None

    DB_SERVER_NAME: str
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSKEY: str


    class Config:
        env_file = ".env"

settings = Settings()
