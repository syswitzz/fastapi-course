from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # checks 1. system env variable, if not found, 2. .env file, 3. default value set here
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
    )

    # generate a secret key: "python3 -c "import secrets; print(secrets.token_hex(32))""
    secret_key: SecretStr   # SecretStr wont leak the value in logs or when printed
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30   


settings = Settings()   # Loaded from .env file

