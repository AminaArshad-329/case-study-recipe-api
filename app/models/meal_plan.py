from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DayOfWeek(str, PyEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class MealSlot(str, PyEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="meal_plans")  # noqa: F821
    entries: Mapped[list["MealPlanEntry"]] = relationship(
        back_populates="meal_plan", cascade="all, delete-orphan"
    )


class MealPlanEntry(Base):
    __tablename__ = "meal_plan_entries"
    __table_args__ = (
        UniqueConstraint(
            "meal_plan_id",
            "day_of_week",
            "meal_slot",
            name="uq_meal_plan_entries_day_slot",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meal_plan_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id"), nullable=False
    )
    day_of_week: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    meal_slot: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    meal_plan: Mapped["MealPlan"] = relationship(back_populates="entries")
    recipe: Mapped["Recipe"] = relationship()  # noqa: F821
