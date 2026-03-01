import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.services.auth import hash_password


async def seed_database(db: AsyncSession) -> None:
    """Seed the database with sample data if it's empty."""
    result = await db.execute(select(User))
    if result.scalars().first() is not None:
        return  # Already seeded

    data_path = Path(__file__).parent / "data.json"
    with open(data_path) as f:
        data = json.load(f)

    # Create users
    user_map = {}
    for user_data in data["users"]:
        user = User(
            username=user_data["username"],
            hashed_password=hash_password(user_data["password"]),
        )
        db.add(user)
        await db.flush()
        user_map[user_data["username"]] = user

    # Create recipes with ingredients
    for recipe_data in data["recipes"]:
        recipe = Recipe(
            title=recipe_data["title"],
            description=recipe_data["description"],
            cuisine=recipe_data["cuisine"],
            prep_time_minutes=recipe_data["prep_time_minutes"],
            servings=recipe_data["servings"],
            user_id=user_map[recipe_data["owner"]].id,
        )
        db.add(recipe)
        await db.flush()

        for ing_data in recipe_data["ingredients"]:
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name=ing_data["name"],
                quantity=ing_data["quantity"],
                unit=ing_data["unit"],
            )
            db.add(ingredient)

    await db.commit()
