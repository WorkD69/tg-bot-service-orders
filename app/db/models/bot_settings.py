from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BotSettings(Base):
    """Key-value store for runtime-configurable business parameters.

    All values are stored as TEXT. Callers are responsible for type conversion
    (SettingsService.get_int / get_float). This keeps the schema simple and
    avoids adding columns for every new setting in the future.
    """

    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BotSettings key={self.key!r} value={self.value!r}>"
