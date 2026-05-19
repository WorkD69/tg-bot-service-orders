"""remove_avito_fields: drop source, campaign (users) and followup_sent_at (orders)

Revision ID: 0013_remove_avito_fields
Revises: 0012_file_captions
Create Date: 2026-04-15 00:00:00.000000

These columns were Avito-specific and are no longer referenced in the codebase.
Dropping them makes the schema consistent with the current models.
"""
import sqlalchemy as sa
from alembic import op

revision = "0013_remove_avito_fields"
down_revision = "0012_file_captions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove Avito traffic-source tracking from users
    op.drop_column("users", "source")
    op.drop_column("users", "campaign")

    # Remove follow-up scheduling field from orders
    op.drop_column("orders", "followup_sent_at")


def downgrade() -> None:
    # Restore orders.followup_sent_at
    op.add_column(
        "orders",
        sa.Column("followup_sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Restore users.campaign
    op.add_column(
        "users",
        sa.Column("campaign", sa.String(), nullable=True),
    )

    # Restore users.source (was NOT NULL with default "unknown")
    op.add_column(
        "users",
        sa.Column("source", sa.String(), nullable=False, server_default="unknown"),
    )
    # After adding the column back, remove the server_default
    # (was set only to satisfy NOT NULL for existing rows on restore)
    op.alter_column("users", "source", server_default=None)
