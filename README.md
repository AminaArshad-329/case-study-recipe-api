# Recipe Sharing API

A recipe sharing platform API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for PostgreSQL)

## Quick Start

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (includes dev dependencies for testing)
pip install -e ".[dev]"

# Copy local environment defaults
cp .env.example .env

# Start the PostgreSQL database
docker compose up -d db

# Apply database migrations
alembic upgrade head

# Run the API server (auto-seeds sample data on first start)
uvicorn app.main:app --reload

# API docs: http://localhost:8000/docs
```

## Running Tests

Tests use a file-backed SQLite database with foreign-key checks enabled, so no PostgreSQL setup is needed:

```bash
pytest
```

## Project Structure

```
app/
├── api/v1/          # API endpoints and routing
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
├── repositories/    # Data access layer
└── seed/            # Sample data for development
```

## API Endpoints

### Auth
- `POST /api/v1/auth/register` — Create a new account
- `POST /api/v1/auth/login` — Get an access token

### Recipes
- `GET /api/v1/recipes/` — List all recipes (paginated)
- `GET /api/v1/recipes/{id}` — Get a recipe with ingredients
- `POST /api/v1/recipes/` — Create a recipe (auth required)
- `PUT /api/v1/recipes/{id}` — Update a recipe (owner only)
- `DELETE /api/v1/recipes/{id}` — Delete a recipe (owner only)

### Meal Plans
- `POST /api/v1/meal-plans/` — Create a new meal plan
- `GET /api/v1/meal-plans/{id}` — Get a meal plan with recipes
- `GET /api/v1/meal-plans/{id}/shopping-list` — Generate aggregated shopping list
- `PUT /api/v1/meal-plans/{id}` — Update a meal plan (owner only)
- `DELETE /api/v1/meal-plans/{id}` — Delete a meal plan (owner only)

## Documentation

For a detailed breakdown of the solution:
- [ARCHITECTURE.md](ARCHITECTURE.md) — Data model, aggregation algorithm, and scaling considerations.
- [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) — Summary of implemented features and audit of original code issues.

## Seed Data

On first startup, the API seeds 12 sample recipes across various cuisines with two demo accounts:

| Username | Password |
|----------|----------|
| `chef_maria` | `password123` |
| `home_cook_bob` | `password123` |

## Docker

To run the full stack with Docker:

```bash
docker compose up --build
```

This starts both PostgreSQL and the API server. If you run the API directly on the host instead of via Compose, keep the local `.env` pointed at `localhost:5432`.
