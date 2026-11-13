"""Persist payment intents and their idempotency/lifecycle state.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mandates", sa.Column("currency", sa.String(length=16), nullable=False, server_default="RLUSD"))
    op.add_column("mandates", sa.Column("issuer", sa.String(length=64), nullable=True))
    op.add_column("mandates", sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    ))
    op.add_column("mandates", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("approved_payees", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        "payment_intents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("mandate_version", sa.Integer(), nullable=True),
        sa.Column("payee", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("issuer", sa.String(length=64), nullable=True),
        sa.Column("network", sa.String(length=16), nullable=False, server_default="testnet"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="api"),
        sa.Column("source_reference", sa.String(length=160), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("verdict", sa.String(length=24), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("tx_hash", sa.String(length=64), nullable=True),
        sa.Column("ledger_result", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_intents_idempotency_key"),
    )
    op.create_index("ix_payment_intents_payee", "payment_intents", ["payee"])
    op.create_index("ix_payment_intents_status", "payment_intents", ["status"])
    op.create_index("ix_payment_intents_verdict", "payment_intents", ["verdict"])
    op.create_index("ix_payment_intents_created_at", "payment_intents", ["created_at"])
    op.create_index("ix_payment_intents_source_reference", "payment_intents", ["source_reference"])
    with op.batch_alter_table("audit_log") as batch:
        batch.add_column(sa.Column("intent_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("source_reference", sa.String(length=160), nullable=True))
        batch.add_column(sa.Column("mandate_version", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_audit_log_intent_id", "payment_intents", ["intent_id"], ["id"])
    op.create_index("ix_audit_log_intent_id", "audit_log", ["intent_id"])
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intent_id", sa.Integer(), sa.ForeignKey("payment_intents.id"), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("decision", sa.String(length=24), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approvals_intent_id", "approvals", ["intent_id"])
    op.create_index("ix_approvals_created_at", "approvals", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_approvals_created_at", table_name="approvals")
    op.drop_index("ix_approvals_intent_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_index("ix_audit_log_intent_id", table_name="audit_log")
    with op.batch_alter_table("audit_log") as batch:
        batch.drop_constraint("fk_audit_log_intent_id", type_="foreignkey")
        batch.drop_column("mandate_version")
        batch.drop_column("source_reference")
        batch.drop_column("intent_id")
    op.drop_index("ix_payment_intents_source_reference", table_name="payment_intents")
    op.drop_index("ix_payment_intents_created_at", table_name="payment_intents")
    op.drop_index("ix_payment_intents_verdict", table_name="payment_intents")
    op.drop_index("ix_payment_intents_status", table_name="payment_intents")
    op.drop_index("ix_payment_intents_payee", table_name="payment_intents")
    op.drop_table("payment_intents")
    op.drop_column("approved_payees", "active")
    op.drop_column("mandates", "updated_at")
    op.drop_column("mandates", "issuer")
    op.drop_column("mandates", "version")
    op.drop_column("mandates", "currency")
