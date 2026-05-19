from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str
    webhook_base_url: str
    webhook_path: str = "/telegram/webhook"
    webhook_secret: str

    # Database
    database_url: str  # postgresql+asyncpg://...

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Bot roles
    operator_group_id: int
    admin_telegram_id: int
    # Bootstrap owner — auto-promoted to owner role on first /start (no second account needed)
    owner_telegram_id: int | None = None

    # Payouts (fallback defaults — will be overridden by BotSettings in a later step)
    operator_payout_percent: float = 70.0
    admin_payout_percent: float = 100.0

    # Robokassa (optional — leave empty to use manual payment mode)
    robokassa_login: str = ""
    robokassa_pass1: str = ""
    robokassa_pass2: str = ""
    robokassa_is_test: bool = True

    # Support contact shown to clients (temporary fallback — will move to BotSettings)
    support_contact: str = ""

    @property
    def webhook_full_url(self) -> str:
        return f"{self.webhook_base_url}{self.webhook_path}"

    @property
    def sync_database_url(self) -> str:
        """Sync URL for APScheduler jobstore (postgresql://, not postgresql+asyncpg://)."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
