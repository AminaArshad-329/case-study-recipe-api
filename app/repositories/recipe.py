from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient


class RecipeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Recipe]:
        result = await self.db.execute(
            select(Recipe)
            .options(selectinload(Recipe.ingredients))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Recipe.id)))
        return result.scalar_one()

    async def get_existing_ids(self, recipe_ids: list[int]) -> set[int]:
        if not recipe_ids:
            return set()

        result = await self.db.execute(select(Recipe.id).where(Recipe.id.in_(recipe_ids)))
        return set(result.scalars().all())

    async def get_by_id(self, recipe_id: int) -> Recipe | None:
        result = await self.db.execute(
            select(Recipe)
            .options(selectinload(Recipe.ingredients))
            .where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> list[Recipe]:
        result = await self.db.execute(
            select(Recipe)
            .where(Recipe.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, recipe: Recipe) -> Recipe:
        self.db.add(recipe)
        await self.db.flush()
        await self.db.refresh(recipe, attribute_names=["ingredients"])
        return recipe

    async def update(self, recipe: Recipe) -> Recipe:
        await self.db.flush()
        await self.db.refresh(recipe)
        return recipe

    async def delete(self, recipe: Recipe) -> None:
        await self.db.delete(recipe)
        await self.db.flush()

    async def get_ingredients(self, recipe_id: int) -> list[Ingredient]:
        result = await self.db.execute(
            select(Ingredient).where(Ingredient.recipe_id == recipe_id)
        )
        return list(result.scalars().all())
