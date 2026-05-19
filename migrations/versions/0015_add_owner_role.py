"""add_owner_role: extend userrole enum with 'owner' value

Revision ID: 0015_add_owner_role
Revises: 0014_add_bot_settings
Create Date: 2026-04-16 00:00:00.000000

PostgreSQL does not allow adding enum values inside a transaction.
We use autocommit_block() to execute ALTER TYPE outside the transaction.

Downgrade note:
    PostgreSQL does not support removing enum values once added.
    The downgrade() is a no-op — use it only if you recreate the type from scratch,
    which is out of scope for this project.
"""
from alembic import op

revision = "0015_add_owner_role"
down_revision = "0014_add_bot_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ADD VALUE must run outside a transaction in PostgreSQL
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'owner'")


def downgrade() -> None:
    # PostgreSQL does not support DROP VALUE for enum types.
    # A full downgrade would require recreating the type and migrating data —
    # intentionally left as a no-op for this project.
    pass
