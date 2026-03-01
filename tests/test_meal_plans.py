import pytest
from httpx import AsyncClient


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

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

async def _create_recipe(client: AsyncClient, headers: dict, title: str = "Test Recipe", ingredients: list | None = None) -> int:
    """Helper to create a recipe and return its ID."""
    if ingredients is None:
        ingredients = [
            {"name": "flour", "quantity": 200, "unit": "g"},
            {"name": "egg", "quantity": 2, "unit": "pieces"},
        ]
    resp = await client.post(
        "/api/v1/recipes/",
        json={
            "title": title,
            "cuisine": "Test",
            "servings": 2,
            "ingredients": ingredients,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_meal_plan(client: AsyncClient, headers: dict, recipe_ids: list[int], name: str = "Weekly Plan") -> dict:
    """Helper to create a meal plan with given recipe IDs spread across days."""
    entries = []
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    slots = ["breakfast", "lunch", "dinner"]
    for i, rid in enumerate(recipe_ids):
        entries.append({
            "recipe_id": rid,
            "day_of_week": days[i % 7],
            "meal_slot": slots[i % 3],
        })
    resp = await client.post(
        "/api/v1/meal-plans/",
        json={"name": name, "entries": entries},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ------------------------------------------------------------------ #
#  Create                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_create_meal_plan(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    data = await _create_meal_plan(client, auth_headers, [recipe_id])
    assert data["name"] == "Weekly Plan"
    assert len(data["entries"]) == 1
    assert data["entries"][0]["recipe_id"] == recipe_id
    assert data["entries"][0]["recipe_title"] == "Test Recipe"


@pytest.mark.asyncio
async def test_create_meal_plan_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/meal-plans/",
        json={"name": "No Auth Plan", "entries": []},
    )
    assert resp.status_code == 401


# ------------------------------------------------------------------ #
#  Get                                                                #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_get_meal_plan(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Weekly Plan"
    assert len(data["entries"]) == 1


@pytest.mark.asyncio
async def test_get_meal_plan_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/meal-plans/9999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_meal_plan_not_owner(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    other_headers = await _register_and_login(client, "otheruser")

    resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}",
        headers=other_headers,
    )
    assert resp.status_code == 403


# ------------------------------------------------------------------ #
#  Update                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_update_meal_plan_name(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    resp = await client.put(
        f"/api/v1/meal-plans/{created['id']}",
        json={"name": "Updated Plan"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Plan"


@pytest.mark.asyncio
async def test_update_meal_plan_entries(client: AsyncClient, auth_headers: dict):
    recipe1 = await _create_recipe(client, auth_headers, title="Recipe 1")
    recipe2 = await _create_recipe(client, auth_headers, title="Recipe 2")
    created = await _create_meal_plan(client, auth_headers, [recipe1])

    resp = await client.put(
        f"/api/v1/meal-plans/{created['id']}",
        json={
            "entries": [
                {"recipe_id": recipe2, "day_of_week": "friday", "meal_slot": "dinner"},
            ]
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["recipe_id"] == recipe2


@pytest.mark.asyncio
async def test_update_meal_plan_not_owner(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    other_headers = await _register_and_login(client, "updater")

    resp = await client.put(
        f"/api/v1/meal-plans/{created['id']}",
        json={"name": "Stolen Plan"},
        headers=other_headers,
    )
    assert resp.status_code == 403


# ------------------------------------------------------------------ #
#  Delete                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_delete_meal_plan(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    resp = await client.delete(
        f"/api/v1/meal-plans/{created['id']}",
        headers=auth_headers,
    )
    assert resp.status_code == 204

    # Confirm deletion
    get_resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_meal_plan_not_owner(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    other_headers = await _register_and_login(client, "deleter")

    resp = await client.delete(
        f"/api/v1/meal-plans/{created['id']}",
        headers=other_headers,
    )
    assert resp.status_code == 403


# ------------------------------------------------------------------ #
#  Shopping List                                                      #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_shopping_list_aggregation(client: AsyncClient, auth_headers: dict):
    """
    Two recipes that share 'egg' ingredient — quantities should be summed.
    Recipe A: flour 200g, egg 2 pieces
    Recipe B: sugar 100g, egg 4 pieces
    Expected: egg 6 pieces, flour 200g, sugar 100g
    """
    recipe_a = await _create_recipe(client, auth_headers, title="Recipe A", ingredients=[
        {"name": "flour", "quantity": 200, "unit": "g"},
        {"name": "egg", "quantity": 2, "unit": "pieces"},
    ])
    recipe_b = await _create_recipe(client, auth_headers, title="Recipe B", ingredients=[
        {"name": "sugar", "quantity": 100, "unit": "g"},
        {"name": "egg", "quantity": 4, "unit": "pieces"},
    ])

    created = await _create_meal_plan(client, auth_headers, [recipe_a, recipe_b])

    resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}/shopping-list",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    items_dict = {item["name"]: item for item in items}

    assert items_dict["egg"]["quantity"] == 6
    assert items_dict["egg"]["unit"] == "pieces"
    assert items_dict["flour"]["quantity"] == 200
    assert items_dict["sugar"]["quantity"] == 100


@pytest.mark.asyncio
async def test_shopping_list_empty_plan(client: AsyncClient, auth_headers: dict):
    """Shopping list for a plan with no entries should return an empty list."""
    resp = await client.post(
        "/api/v1/meal-plans/",
        json={"name": "Empty Plan", "entries": []},
        headers=auth_headers,
    )
    plan_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/meal-plans/{plan_id}/shopping-list",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_shopping_list_not_owner(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    other_headers = await _register_and_login(client, "snooper")

    resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}/shopping-list",
        headers=other_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_meal_plan_rejects_missing_recipe_ids(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Broken Plan",
            "entries": [
                {"recipe_id": 9999, "day_of_week": "monday", "meal_slot": "breakfast"},
            ],
        },
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == {
        "message": "Meal plan references unknown recipes",
        "missing_recipe_ids": [9999],
    }


@pytest.mark.asyncio
async def test_update_meal_plan_rejects_missing_recipe_ids(client: AsyncClient, auth_headers: dict):
    recipe_id = await _create_recipe(client, auth_headers)
    created = await _create_meal_plan(client, auth_headers, [recipe_id])

    resp = await client.put(
        f"/api/v1/meal-plans/{created['id']}",
        json={
            "entries": [
                {"recipe_id": 9999, "day_of_week": "monday", "meal_slot": "breakfast"},
            ]
        },
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == {
        "message": "Meal plan references unknown recipes",
        "missing_recipe_ids": [9999],
    }


@pytest.mark.asyncio
async def test_create_meal_plan_rejects_duplicate_day_slot(client: AsyncClient, auth_headers: dict):
    recipe1 = await _create_recipe(client, auth_headers, title="Recipe 1")
    recipe2 = await _create_recipe(client, auth_headers, title="Recipe 2")

    resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Conflicting Plan",
            "entries": [
                {"recipe_id": recipe1, "day_of_week": "monday", "meal_slot": "breakfast"},
                {"recipe_id": recipe2, "day_of_week": "monday", "meal_slot": "breakfast"},
            ],
        },
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == {
        "message": "Meal plan contains duplicate day/slot assignments",
        "duplicate_slots": [{"day_of_week": "monday", "meal_slot": "breakfast"}],
    }


@pytest.mark.asyncio
async def test_update_meal_plan_rejects_duplicate_day_slot(client: AsyncClient, auth_headers: dict):
    recipe1 = await _create_recipe(client, auth_headers, title="Recipe 1")
    recipe2 = await _create_recipe(client, auth_headers, title="Recipe 2")
    created = await _create_meal_plan(client, auth_headers, [recipe1])

    resp = await client.put(
        f"/api/v1/meal-plans/{created['id']}",
        json={
            "entries": [
                {"recipe_id": recipe1, "day_of_week": "monday", "meal_slot": "breakfast"},
                {"recipe_id": recipe2, "day_of_week": "monday", "meal_slot": "breakfast"},
            ]
        },
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == {
        "message": "Meal plan contains duplicate day/slot assignments",
        "duplicate_slots": [{"day_of_week": "monday", "meal_slot": "breakfast"}],
    }


@pytest.mark.asyncio
async def test_shopping_list_normalizes_name_and_unit_casing(client: AsyncClient, auth_headers: dict):
    recipe_a = await _create_recipe(
        client,
        auth_headers,
        title="Recipe A",
        ingredients=[{"name": " Egg ", "quantity": 2, "unit": " Pieces "}],
    )
    recipe_b = await _create_recipe(
        client,
        auth_headers,
        title="Recipe B",
        ingredients=[{"name": "egg", "quantity": 4, "unit": "pieces"}],
    )

    created = await _create_meal_plan(client, auth_headers, [recipe_a, recipe_b])

    resp = await client.get(
        f"/api/v1/meal-plans/{created['id']}/shopping-list",
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert resp.json() == [{"name": "Egg", "quantity": 6.0, "unit": "Pieces"}]
