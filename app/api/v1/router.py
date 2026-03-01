from fastapi import APIRouter

from app.api.v1.endpoints import auth, recipes, meal_plans

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(recipes.router)
api_router.include_router(meal_plans.router)
