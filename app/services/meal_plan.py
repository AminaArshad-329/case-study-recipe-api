from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal_plan import MealPlan, MealPlanEntry
from app.models.user import User
from app.repositories.meal_plan import MealPlanRepository
from app.repositories.recipe import RecipeRepository
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    MealPlanEntryResponse,
    ShoppingListItem,
    MealPlanEntryCreate,
)


class MealPlanService:
    def __init__(self, db: AsyncSession):
        self.repo = MealPlanRepository(db)
        self.recipe_repo = RecipeRepository(db)
        self.db = db

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _check_ownership(self, meal_plan: MealPlan, user: User) -> None:
        """Raise 403 if the user does not own the meal plan."""
        if meal_plan.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own meal plans",
            )

    async def _validate_entries(self, entries: list[MealPlanEntryCreate]) -> None:
        if not entries:
            return

        seen_slots: set[tuple[str, str]] = set()
        duplicate_slots: set[tuple[str, str]] = set()
        for entry in entries:
            slot = (entry.day_of_week.value, entry.meal_slot.value)
            if slot in seen_slots:
                duplicate_slots.add(slot)
            else:
                seen_slots.add(slot)

        if duplicate_slots:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Meal plan contains duplicate day/slot assignments",
                    "duplicate_slots": [
                        {"day_of_week": day_of_week, "meal_slot": meal_slot}
                        for day_of_week, meal_slot in sorted(duplicate_slots)
                    ],
                },
            )

        recipe_ids = sorted({entry.recipe_id for entry in entries})
        existing_recipe_ids = await self.recipe_repo.get_existing_ids(recipe_ids)
        missing_recipe_ids = [recipe_id for recipe_id in recipe_ids if recipe_id not in existing_recipe_ids]
        if missing_recipe_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Meal plan references unknown recipes",
                    "missing_recipe_ids": missing_recipe_ids,
                },
            )

    @staticmethod
    def _to_response(meal_plan: MealPlan) -> MealPlanResponse:
        """Convert a MealPlan ORM object to the response schema."""
        return MealPlanResponse(
            id=meal_plan.id,
            name=meal_plan.name,
            user_id=meal_plan.user_id,
            created_at=meal_plan.created_at,
            updated_at=meal_plan.updated_at,
            entries=[
                MealPlanEntryResponse(
                    id=entry.id,
                    recipe_id=entry.recipe_id,
                    recipe_title=entry.recipe.title if entry.recipe else None,
                    day_of_week=entry.day_of_week,
                    meal_slot=entry.meal_slot,
                )
                for entry in meal_plan.entries
            ],
        )

    # ------------------------------------------------------------------ #
    #  CRUD                                                               #
    # ------------------------------------------------------------------ #

    async def create_meal_plan(self, data: MealPlanCreate, user: User) -> MealPlanResponse:
        await self._validate_entries(data.entries)

        meal_plan = MealPlan(name=data.name, user_id=user.id)

        for entry_data in data.entries:
            entry = MealPlanEntry(
                recipe_id=entry_data.recipe_id,
                day_of_week=entry_data.day_of_week.value,
                meal_slot=entry_data.meal_slot.value,
            )
            meal_plan.entries.append(entry)

        meal_plan = await self.repo.create(meal_plan)
        return self._to_response(meal_plan)

    async def get_meal_plan(self, meal_plan_id: int, user: User) -> MealPlanResponse:
        meal_plan = await self.repo.get_by_id(meal_plan_id)
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found",
            )
        self._check_ownership(meal_plan, user)
        return self._to_response(meal_plan)

    async def update_meal_plan(
        self, meal_plan_id: int, data: MealPlanUpdate, user: User
    ) -> MealPlanResponse:
        meal_plan = await self.repo.get_by_id(meal_plan_id)
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found",
            )
        self._check_ownership(meal_plan, user)

        if data.name is not None:
            meal_plan.name = data.name

        if data.entries is not None:
            await self._validate_entries(data.entries)

            # Remove old entries
            for entry in meal_plan.entries:
                await self.db.delete(entry)
            await self.db.flush()

            meal_plan.entries = []
            for entry_data in data.entries:
                entry = MealPlanEntry(
                    recipe_id=entry_data.recipe_id,
                    day_of_week=entry_data.day_of_week.value,
                    meal_slot=entry_data.meal_slot.value,
                    meal_plan_id=meal_plan.id,
                )
                meal_plan.entries.append(entry)

        meal_plan = await self.repo.update(meal_plan)
        return self._to_response(meal_plan)

    async def delete_meal_plan(self, meal_plan_id: int, user: User) -> None:
        meal_plan = await self.repo.get_by_id(meal_plan_id)
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found",
            )
        self._check_ownership(meal_plan, user)
        await self.repo.delete(meal_plan)

    # ------------------------------------------------------------------ #
    #  Shopping List Aggregation                                          #
    # ------------------------------------------------------------------ #

    async def get_shopping_list(self, meal_plan_id: int, user: User) -> list[ShoppingListItem]:
        """
        Collect all ingredients from every recipe in the meal plan,
        then aggregate duplicates (same name + same unit) by summing quantities.
        """
        meal_plan = await self.repo.get_by_id_with_ingredients(meal_plan_id)
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found",
            )
        self._check_ownership(meal_plan, user)

        # Aggregate: key = (normalised name, normalised unit)
        aggregated: dict[tuple[str, str | None], float | None] = defaultdict(lambda: None)
        # Keep track of the original casing for display
        display_names: dict[tuple[str, str | None], tuple[str, str | None]] = {}

        for entry in meal_plan.entries:
            if not entry.recipe:
                continue
            for ingredient in entry.recipe.ingredients:
                key = (
                    ingredient.name.strip().lower(),
                    ingredient.unit.strip().lower() if ingredient.unit else None,
                )
                # Store display name on first encounter
                if key not in display_names:
                    display_names[key] = (
                        ingredient.name.strip(),
                        ingredient.unit.strip() if ingredient.unit else None,
                    )

                if ingredient.quantity is not None:
                    current = aggregated[key]
                    aggregated[key] = (current or 0) + ingredient.quantity
                else:
                    # If we haven't recorded anything yet, keep None
                    if key not in aggregated:
                        aggregated[key] = None

        shopping_list = []
        for key, quantity in aggregated.items():
            name, unit = display_names[key]
            shopping_list.append(ShoppingListItem(name=name, quantity=quantity, unit=unit))

        # Sort alphabetically for consistent output
        shopping_list.sort(key=lambda item: item.name.lower())
        return shopping_list
