from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.v1.dependencies import get_current_user
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    ShoppingListItem,
)
from app.services.meal_plan import MealPlanService

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


@router.post("/", response_model=MealPlanResponse, status_code=201)
async def create_meal_plan(
    data: MealPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new meal plan for the authenticated user."""
    service = MealPlanService(db)
    return await service.create_meal_plan(data, current_user)


@router.get("/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a meal plan with its assigned recipes (owner only)."""
    service = MealPlanService(db)
    return await service.get_meal_plan(meal_plan_id, current_user)


@router.get("/{meal_plan_id}/shopping-list", response_model=list[ShoppingListItem])
async def get_shopping_list(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate an aggregated shopping list from all recipes in the meal plan."""
    service = MealPlanService(db)
    return await service.get_shopping_list(meal_plan_id, current_user)


@router.put("/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    meal_plan_id: int,
    data: MealPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a meal plan (owner only)."""
    service = MealPlanService(db)
    return await service.update_meal_plan(meal_plan_id, data, current_user)


@router.delete("/{meal_plan_id}", status_code=204)
async def delete_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a meal plan (owner only)."""
    service = MealPlanService(db)
    await service.delete_meal_plan(meal_plan_id, current_user)
