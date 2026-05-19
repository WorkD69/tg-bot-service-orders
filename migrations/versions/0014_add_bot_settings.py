"""add_bot_settings: create bot_settings table with default values

Revision ID: 0014_add_bot_settings
Revises: 0013_remove_avito_fields
Create Date: 2026-04-15 00:00:00.000000

Creates the key-value store for runtime-configurable business parameters.
Default values are inserted with ON CONFLICT DO NOTHING so re-running the
migration (e.g. in tests) is always safe and does not overwrite user changes.
"""
import sqlalchemy as sa
from alembic import op

revision = "0014_add_bot_settings"
down_revision = "0013_remove_avito_fields"
branch_labels = None
depends_on = None

# Default settings inserted on first deploy
_DEFAULTS = [
    ("service_name",            "Сервис заявок"),
    ("welcome_text",            "Добро пожаловать! Выберите действие:"),
    ("support_contact",         ""),
    ("payment_requisites",      ""),
    ("max_active_orders",       "5"),
    ("auction_timeout_minutes", "120"),
    ("operator_payout_percent", "70"),
]


def upgrade() -> None:
    op.create_table(
        "bot_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Insert defaults; ON CONFLICT DO NOTHING = safe for repeated runs
    bot_settings = sa.table(
        "bot_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.bulk_insert(
        bot_settings,
        [{"key": k, "value": v} for k, v in _DEFAULTS],
    )


def downgrade() -> None:
    op.drop_table("bot_settings")
