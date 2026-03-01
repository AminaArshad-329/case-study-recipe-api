"""Add meal plan tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-01 22:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_meal_plans_id", "meal_plans", ["id"])

    op.create_table(
        "meal_plan_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("meal_plan_id", sa.Integer(), sa.ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("day_of_week", sa.String(20), nullable=False),
        sa.Column("meal_slot", sa.String(20), nullable=False),
        sa.UniqueConstraint("meal_plan_id", "day_of_week", "meal_slot", name="uq_meal_plan_entries_day_slot"),
    )
    op.create_index("ix_meal_plan_entries_id", "meal_plan_entries", ["id"])


def downgrade() -> None:
    op.drop_index("ix_meal_plan_entries_id", table_name="meal_plan_entries")
    op.drop_table("meal_plan_entries")
    op.drop_index("ix_meal_plans_id", table_name="meal_plans")
    op.drop_table("meal_plans")