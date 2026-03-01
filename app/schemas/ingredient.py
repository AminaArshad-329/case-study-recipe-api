from pydantic import BaseModel, Field


class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float | None = None
    unit: str | None = Field(None, max_length=50)


class IngredientResponse(BaseModel):
    id: int
    name: str
    quantity: float | None
    unit: str | None

    model_config = {"from_attributes": True}
