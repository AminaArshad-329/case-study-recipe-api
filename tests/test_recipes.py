import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient, username: str, password: str = "password123"
) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


async def _create_meal_plan_for_recipe(client: AsyncClient, headers: dict, recipe_id: int) -> int:
    response = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Weekly Plan",
            "entries": [
                {"recipe_id": recipe_id, "day_of_week": "monday", "meal_slot": "dinner"},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_recipe(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/recipes/",
        json={
            "title": "Test Recipe",
            "description": "A test recipe",
            "cuisine": "Test",
            "prep_time_minutes": 30,
            "servings": 4,
            "ingredients": [
                {"name": "flour", "quantity": 200, "unit": "g"},
                {"name": "sugar", "quantity": 100, "unit": "g"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Recipe"
    assert len(data["ingredients"]) == 2


@pytest.mark.asyncio
async def test_create_recipe_unauthenticated(client: AsyncClient):
    response = await client.post(
        "/api/v1/recipes/",
        json={"title": "Test Recipe"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_recipe(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={
            "title": "Fetchable Recipe",
            "cuisine": "Italian",
            "ingredients": [{"name": "pasta", "quantity": 300, "unit": "g"}],
        },
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Fetchable Recipe"
    assert len(data["ingredients"]) == 1


@pytest.mark.asyncio
async def test_get_recipe_not_found(client: AsyncClient):
    response = await client.get("/api/v1/recipes/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_recipes(client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await client.post(
            "/api/v1/recipes/",
            json={"title": f"Recipe {i}", "ingredients": []},
            headers=auth_headers,
        )

    response = await client.get("/api/v1/recipes/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_recipes_pagination(client: AsyncClient, auth_headers: dict):
    for i in range(5):
        await client.post(
            "/api/v1/recipes/",
            json={"title": f"Recipe {i}", "ingredients": []},
            headers=auth_headers,
        )

    response = await client.get("/api/v1/recipes/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_recipe(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Old Title", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/recipes/{recipe_id}",
        json={"title": "New Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_recipe_not_owner(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Owner Recipe", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]

    other_headers = await _register_and_login(client, "otheruser")

    response = await client.put(
        f"/api/v1/recipes/{recipe_id}",
        json={"title": "Stolen Title"},
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_recipe(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Delete Me", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/recipes/{recipe_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/recipes/{recipe_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_recipe_not_owner(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Protected Recipe", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]

    other_headers = await _register_and_login(client, "badactor")

    response = await client.delete(
        f"/api/v1/recipes/{recipe_id}",
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_recipe_in_use_returns_409(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Planned Recipe", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]
    await _create_meal_plan_for_recipe(client, auth_headers, recipe_id)

    response = await client.delete(
        f"/api/v1/recipes/{recipe_id}",
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Recipe is assigned to one or more meal plan entries"


@pytest.mark.asyncio
async def test_delete_recipe_succeeds_after_meal_plan_deleted(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/recipes/",
        json={"title": "Temporary Planned Recipe", "ingredients": []},
        headers=auth_headers,
    )
    recipe_id = create_resp.json()["id"]
    meal_plan_id = await _create_meal_plan_for_recipe(client, auth_headers, recipe_id)

    delete_plan_resp = await client.delete(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=auth_headers,
    )
    assert delete_plan_resp.status_code == 204

    delete_recipe_resp = await client.delete(
        f"/api/v1/recipes/{recipe_id}",
        headers=auth_headers,
    )
    assert delete_recipe_resp.status_code == 204
