import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admins: list[int] = field(default_factory=list)
    use_webhook: bool = False

    def __post_init__(self):
        admins_str = os.getenv("BOT_ADMINS", "")
        if admins_str:
            self.admins = [int(x) for x in admins_str.split(",") if x.strip()]

        if not self.token:
            raise ValueError("BOT_TOKEN не установлен")


@dataclass
class DeepSeekConfig:
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "DEEPSEEK_BASE_URL", "https://openrouter.ai/api/v1"
        )
    )
    model: str = field(
        default_factory=lambda: os.getenv(
            "DEEPSEEK_MODEL", "tngtech/deepseek-r1t-chimera:free"
        )
    )

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не установлен")


@dataclass
class AppConfig:
    bot: BotConfig = field(default_factory=BotConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @property
    def is_valid(self) -> bool:
        return bool(self.bot.token and self.deepseek.api_key)


def load_config() -> AppConfig:
    return AppConfig()
