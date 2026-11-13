"""initial schema: mandates, approved payees, audit log

Revision ID: 0001
Revises:
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mandates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("per_payment_cap", sa.Numeric(20, 6), nullable=False),
        sa.Column("daily_cap", sa.Numeric(20, 6), nullable=False),
        sa.Column("max_slippage_pct", sa.Numeric(6, 3), nullable=False),
        sa.Column("large_payment_threshold", sa.Numeric(20, 6), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "approved_payees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mandate_id", sa.Integer(), sa.ForeignKey("mandates.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("xrpl_address", sa.String(64), nullable=False),
    )
    op.create_index("ix_approved_payees_xrpl_address", "approved_payees", ["xrpl_address"])
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payee", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("verdict", sa.String(24), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("tx_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_payee", "audit_log", ["payee"])
    op.create_index("ix_audit_log_verdict", "audit_log", ["verdict"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("approved_payees")
    op.drop_table("mandates")
