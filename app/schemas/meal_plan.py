from datetime import datetime

from pydantic import BaseModel, Field

from app.models.meal_plan import DayOfWeek, MealSlot


# --- Request schemas ---

class MealPlanEntryCreate(BaseModel):
    recipe_id: int
    day_of_week: DayOfWeek
    meal_slot: MealSlot


class MealPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entries: list[MealPlanEntryCreate] = Field(default_factory=list)


class MealPlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    entries: list[MealPlanEntryCreate] | None = None


# --- Response schemas ---

class MealPlanEntryResponse(BaseModel):
    id: int
    recipe_id: int
    recipe_title: str | None = None
    day_of_week: str
    meal_slot: str

    model_config = {"from_attributes": True}


class MealPlanResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    entries: list[MealPlanEntryResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ShoppingListItem(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
