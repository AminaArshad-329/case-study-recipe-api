# Architecture Document

## 1. Data Model Decisions

### Meal Plan Schema
```
meal_plans
├── id (PK)
├── name (VARCHAR 200)
├── user_id (FK → users.id)
├── created_at
└── updated_at

meal_plan_entries
├── id (PK)
├── meal_plan_id (FK → meal_plans.id, CASCADE)
├── recipe_id (FK → recipes.id)
├── day_of_week (VARCHAR 20: monday–sunday)
└── meal_slot (VARCHAR 20: breakfast, lunch, dinner)
```

**Why this design:**

- **Separate `meal_plan_entries` table** — A meal plan has many entries, each linking a specific day+slot to a recipe. This is cleaner than embedding JSON or having 21 columns (7 days × 3 slots). It naturally supports variable slots per day and is easy to query, index, and extend.
- **String columns for `day_of_week` and `meal_slot`** — Stored as VARCHAR(20) for full SQLite and PostgreSQL compatibility. Valid values (monday–sunday, breakfast/lunch/dinner) are enforced at the application layer via Pydantic schemas, keeping migrations portable across databases.
- **`recipe_id` as a FK without CASCADE DELETE** — If a recipe is deleted, the meal plan entry should not silently disappear. In production, this would be handled with a soft-delete or a check constraint.
- **`CASCADE DELETE` on `meal_plan_id`** — When a meal plan is deleted, all its entries are removed automatically.
