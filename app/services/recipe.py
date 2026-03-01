from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.user import User
from app.repositories.meal_plan import MealPlanRepository
from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import RecipeCreate, RecipeUpdate


class RecipeService:
    def __init__(self, db: AsyncSession):
        self.recipe_repo = RecipeRepository(db)
        self.meal_plan_repo = MealPlanRepository(db)
        self.db = db

    async def list_recipes(self, skip: int = 0, limit: int = 20) -> tuple[list[Recipe], int]:
        recipes = await self.recipe_repo.get_all(skip=skip, limit=limit)
        total = await self.recipe_repo.count()
        return recipes, total

    async def get_recipe(self, recipe_id: int) -> Recipe:
        recipe = await self.recipe_repo.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        return recipe

    async def create_recipe(self, data: RecipeCreate, user: User) -> Recipe:
        recipe = Recipe(
            title=data.title,
            description=data.description,
            cuisine=data.cuisine,
            prep_time_minutes=data.prep_time_minutes,
            servings=data.servings,
            user_id=user.id,
        )
        for ing_data in data.ingredients:
            ingredient = Ingredient(
                name=ing_data.name,
                quantity=ing_data.quantity,
                unit=ing_data.unit,
            )
            recipe.ingredients.append(ingredient)

        return await self.recipe_repo.create(recipe)

    async def update_recipe(self, recipe_id: int, data: RecipeUpdate, user: User) -> Recipe:
        recipe = await self.get_recipe(recipe_id)
        if recipe.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own recipes",
            )

        if data.title is not None:
            recipe.title = data.title
        if data.description is not None:
            recipe.description = data.description
        if data.cuisine is not None:
            recipe.cuisine = data.cuisine
        if data.prep_time_minutes is not None:
            recipe.prep_time_minutes = data.prep_time_minutes
        if data.servings is not None:
            recipe.servings = data.servings

        if data.ingredients is not None:
            for ing in recipe.ingredients:
                await self.db.delete(ing)
            await self.db.flush()

            recipe.ingredients = []
            for ing_data in data.ingredients:
                ingredient = Ingredient(
                    name=ing_data.name,
                    quantity=ing_data.quantity,
                    unit=ing_data.unit,
                    recipe_id=recipe.id,
                )
                recipe.ingredients.append(ingredient)

        return await self.recipe_repo.update(recipe)

    async def delete_recipe(self, recipe_id: int, user: User) -> None:
        recipe = await self.get_recipe(recipe_id)
        if recipe.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own recipes",
            )
        if await self.meal_plan_repo.recipe_is_used(recipe_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Recipe is assigned to one or more meal plan entries",
            )
        await self.recipe_repo.delete(recipe)
