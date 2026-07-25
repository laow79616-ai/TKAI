"""Create the namespace-scoped PostgreSQL document storage table."""

from __future__ import annotations

from importlib import import_module

op = import_module("alembic.op")
sa = import_module("sqlalchemy")
postgresql = import_module("sqlalchemy.dialects.postgresql")

revision = "0001_marketplace_documents"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the only table used by the optional document repository."""
    op.create_table(
        "marketplace_documents",
        sa.Column("namespace", sa.String(length=128), nullable=False),
        sa.Column("identifier", sa.String(length=256), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "identifier"),
    )


def downgrade() -> None:
    """Remove the optional PostgreSQL document storage table."""
    op.drop_table("marketplace_documents")
