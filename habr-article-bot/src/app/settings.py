from pydantic_settings import BaseSettings, SettingsConfigDict


def setup_settings():
    settings.habrApiUrl = settings.habrApiUrl.removesuffix("/")


class Settings(BaseSettings):
    botToken: str

    notifyStartStop: bool
    enableWhitelist: bool

    whitelist: list

    habrApiUrl: str

    model_config = SettingsConfigDict(env_file = ".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore
setup_settings()
