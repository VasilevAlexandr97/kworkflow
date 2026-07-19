import os

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent.parent.resolve()


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_url(self):
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def psycopg_connection_url(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: str
    password: str

    @property
    def connection_url(self):
        return f"redis://:{self.password}@{self.host}:{self.port}"

    @property
    def async_connection_url(self):
        return f"async+{self.connection_url}"


@dataclass(frozen=True)
class TelegramBotConfig:
    token: str


@dataclass(frozen=True)
class KworkConfig:
    login: str
    password: str


@dataclass(frozen=True)
class PolzaConfig:
    api_key: str
    base_url: str


@dataclass(frozen=True)
class YookassaConfig:
    shop_id: str
    secret_key: str


@dataclass(frozen=True)
class WebConfig:
    templates_dir: Path = (
        PROJECT_DIR / "src" / "kworkflow" / "web" / "templates"
    )
    static_dir: Path = PROJECT_DIR / "src" / "kworkflow" / "web" / "static"


@dataclass(frozen=True)
class Config:
    postgres: PostgresConfig
    redis: RedisConfig
    telegram_bot: TelegramBotConfig
    kwork: KworkConfig
    polza: PolzaConfig
    yookassa: YookassaConfig
    web: WebConfig
    # project_dir: Path = PROJECT_DIR
    debug: bool = field(default=False)


def get_required_env(env_var: str) -> str:
    value = os.getenv(env_var)
    if not value:
        raise ValueError(f"Environment variable {env_var} is required")
    return value


def get_optional_env(name: str) -> str | None:
    return os.getenv(name)


def get_config() -> Config:
    return Config(
        postgres=PostgresConfig(
            host=get_required_env("POSTGRES_HOST"),
            port=int(get_required_env("POSTGRES_PORT")),
            user=get_required_env("POSTGRES_USER"),
            password=get_required_env("POSTGRES_PASSWORD"),
            database=get_required_env("POSTGRES_DATABASE"),
        ),
        redis=RedisConfig(
            host=get_required_env("REDIS_HOST"),
            port=get_required_env("REDIS_PORT"),
            password=get_required_env("REDIS_PASSWORD"),
        ),
        telegram_bot=TelegramBotConfig(
            token=get_required_env("TELEGRAM_BOT_TOKEN"),
        ),
        kwork=KworkConfig(
            login=get_required_env("KWORK_USERNAME"),
            password=get_required_env("KWORK_PASSWORD"),
        ),
        debug=get_optional_env("DEBUG") in ("True", "true", "1"),
        polza=PolzaConfig(
            api_key=get_required_env("POLZA_API_KEY"),
            base_url=get_required_env("POLZA_BASE_URL"),
        ),
        yookassa=YookassaConfig(
            shop_id=get_required_env("YOOKASSA_SHOP_ID"),
            secret_key=get_required_env("YOOKASSA_SECRET_KEY"),
        ),
        web=WebConfig(),
    )


config = get_config()
