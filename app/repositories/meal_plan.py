from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal_plan import MealPlan, MealPlanEntry
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient


class MealPlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, meal_plan_id: int) -> MealPlan | None:
        """Get a meal plan with entries and their recipe titles eagerly loaded."""
        result = await self.db.execute(
            select(MealPlan)
            .options(
                selectinload(MealPlan.entries).selectinload(MealPlanEntry.recipe)
            )
            .where(MealPlan.id == meal_plan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_ingredients(self, meal_plan_id: int) -> MealPlan | None:
        """Get a meal plan with entries, recipes, AND their ingredients for shopping list."""
        result = await self.db.execute(
            select(MealPlan)
            .options(
                selectinload(MealPlan.entries)
                .selectinload(MealPlanEntry.recipe)
                .selectinload(Recipe.ingredients)
            )
            .where(MealPlan.id == meal_plan_id)
        )
        return result.scalar_one_or_none()

    async def create(self, meal_plan: MealPlan) -> MealPlan:
        self.db.add(meal_plan)
        await self.db.flush()
        await self.db.refresh(meal_plan, attribute_names=["entries"])
        # Eager-load recipe titles for every entry
        for entry in meal_plan.entries:
            await self.db.refresh(entry, attribute_names=["recipe"])
        return meal_plan

    async def update(self, meal_plan: MealPlan) -> MealPlan:
        await self.db.flush()
        # Re-fetch to ensure all attributes (including server-side updated_at) are loaded
        return await self.get_by_id(meal_plan.id)

    async def recipe_is_used(self, recipe_id: int) -> bool:
        result = await self.db.execute(
            select(func.count(MealPlanEntry.id)).where(MealPlanEntry.recipe_id == recipe_id)
        )
        return result.scalar_one() > 0

    async def delete(self, meal_plan: MealPlan) -> None:
        await self.db.delete(meal_plan)
        await self.db.flush()
