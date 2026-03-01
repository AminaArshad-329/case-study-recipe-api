# Backend Developer Case Study — Recipe Sharing API

## Overview

You're joining a team that maintains a **Recipe Sharing Platform**. The existing API provides authentication, recipe CRUD, and ingredient management. Your task is to extend this codebase with a new feature, improve the existing code, and document your architectural decisions.

**Estimated time**: 8–12 hours (you don't need to do it in one sitting)

**What we're evaluating**: Code comprehension, architecture decisions, testing, and written communication — not speed.

---

## Part A — Feature: Meal Planning (70% of effort)

Build a **Meal Planning** feature that lets authenticated users plan their meals for a week and auto-generate a shopping list.

### Required Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/meal-plans` | Create a new meal plan |
| `GET` | `/api/v1/meal-plans/{id}` | Get a meal plan with its assigned recipes |
| `GET` | `/api/v1/meal-plans/{id}/shopping-list` | Auto-generate an aggregated shopping list |
| `PUT` | `/api/v1/meal-plans/{id}` | Update a meal plan |
| `DELETE` | `/api/v1/meal-plans/{id}` | Delete a meal plan |

### Requirements

- A meal plan belongs to the authenticated user who created it
- A meal plan has a name and covers 7 days (Monday–Sunday)
- Each day can have multiple meal slots (e.g., breakfast, lunch, dinner)
- Each meal slot is assigned a recipe from the existing recipes
- The **shopping list endpoint** must:
  - Collect all ingredients from all recipes in the meal plan
  - Aggregate duplicate ingredients (same name + same unit) by summing their quantities
  - Return a clean, consolidated list
- Only the owner can view, update, or delete their meal plans
- Include tests for the new feature using the existing test infrastructure

### Example Shopping List Aggregation

If Monday dinner has "Spaghetti Carbonara" (400g spaghetti, 4 eggs) and Wednesday lunch has "Banana Pancakes" (2 eggs), the shopping list should show:
- spaghetti: 400g
- egg: 6 pieces

---

## Part B — Codebase Improvements (20% of effort)

Review the existing codebase. Make any improvements you consider important for a production deployment. For each change, write a brief comment or commit message explaining **why** you made it.

Focus areas to consider (not an exhaustive list):
- Correctness
- Performance
- Security
- Maintainability

---

## Part C — Architecture Document (10% of effort)

Write a short document (1–2 pages) called `ARCHITECTURE.md` covering:

1. **Data model decisions** — How you modeled meal plans and why
2. **Shopping list aggregation** — How it works, edge cases you considered
3. **Scaling considerations** — What would change if this API served 10,000 concurrent users?
4. **Production readiness** — What would you add before deploying this to production?

---

## Submission Guidelines

1. Create a Git repository with your changes
2. Use meaningful commit messages — we read commit history
3. Include a working `README.md` with setup instructions
4. Make sure all tests pass: `pytest`
5. Submit the repository link

---

## Setup

```bash
# Clone and enter the project
cd case-study-recipe-api

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start the database
docker compose up -d db

# Run the API (auto-seeds sample data on first start)
uvicorn app.main:app --reload

# Run tests
pytest

# API docs available at http://localhost:8000/docs
```

### Seed Accounts

The API auto-seeds sample data on first start. You can use these accounts:

| Username | Password |
|----------|----------|
| `chef_maria` | `password123` |
| `home_cook_bob` | `password123` |

---

## Questions?

If anything is unclear, make a reasonable assumption and document it in your architecture doc. We value seeing how you handle ambiguity.
