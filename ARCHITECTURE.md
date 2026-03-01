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
├── day_of_week (ENUM: monday–sunday)
└── meal_slot (ENUM: breakfast, lunch, dinner, snack)
```

**Why this design:**

- **Separate `meal_plan_entries` table** — A meal plan has many entries, each linking a specific day+slot to a recipe. This is cleaner than embedding JSON or having 21 columns (7 days × 3 slots). It naturally supports variable slots per day and is easy to query, index, and extend.
- **Enums for `day_of_week` and `meal_slot`** — Prevents invalid data at the database level. Using PostgreSQL enum types (or SQLAlchemy `Enum` mapped to varchar for SQLite compatibility in tests) keeps the data clean without application-layer validation only.
- **`recipe_id` as a FK without CASCADE DELETE** — If a recipe is deleted, the meal plan entry should not silently disappear. In production, this would be handled with a soft-delete or a check constraint.
- **`CASCADE DELETE` on `meal_plan_id`** — When a meal plan is deleted, all its entries are removed automatically.

---

## 2. Shopping List Aggregation

### How It Works

1. Eager-load the meal plan with all entries → recipes → ingredients in a single query using `selectinload` (3-level nested eager loading).
2. Iterate over every ingredient in every recipe in every entry.
3. Group by a normalised key: `(name.lower().strip(), unit.lower().strip())`.
4. Sum quantities for matching keys.
5. Return a sorted list of `ShoppingListItem` objects.

### Edge Cases Considered

| Edge Case | Handling |
|---|---|
| Same ingredient, different casing ("Egg" vs "egg") | Normalised to lowercase for grouping |
| Same ingredient, different units ("g" vs "kg") | Treated as separate items — unit conversion is out of scope |
| Ingredient with `quantity = None` | Preserved as-is; does not break summation |
| Empty meal plan (no entries) | Returns an empty list `[]` |
| Recipe referenced by multiple entries | Each occurrence adds to the total quantity |

### Time Complexity

`O(E × I)` where E = number of entries and I = average ingredients per recipe. For a weekly plan (~21 entries max), this is trivially fast.

---

## 3. Scaling Considerations (10,000 Concurrent Users)

### Database Layer
- **Connection pooling**: Switch from default SQLAlchemy pool to `asyncpg` with bounded pool sizes (`pool_size=20`, `max_overflow=10`). Consider PgBouncer for connection multiplexing.
- **Read replicas**: Route read-heavy endpoints (list recipes, get shopping list) to read replicas.
- **Indexing**: Add composite index on `(meal_plan_id, day_of_week)` for entry lookups. The FK indexes already cover most query patterns.

### Application Layer
- **Caching**: Cache shopping list results in Redis with a TTL. Invalidate on meal plan update. Recipe data changes infrequently — cache aggressively.
- **Rate limiting**: Add per-user rate limits to prevent abuse (e.g., `slowapi` middleware).
- **Horizontal scaling**: The API is stateless — deploy multiple instances behind a load balancer.

### Infrastructure
- **Container orchestration**: Move from Docker Compose to Kubernetes for auto-scaling, health checks, and rolling deployments.
- **CDN/API Gateway**: Add an API gateway (e.g., Kong, AWS API Gateway) for throttling, authentication offloading, and request routing.

---

## 4. Production Readiness

### Must-Have Before Deployment

| Area | What to Add |
|---|---|
| **Secrets management** | Move `SECRET_KEY` and `DATABASE_URL` to a vault (e.g., AWS Secrets Manager, HashiCorp Vault). Never hardcode in source. |
| **Database migrations** | Alembic migrations are now the source of truth for schema changes. In production, run them as a deployment step or job instead of inside the API container startup path. |
| **Logging** | Structured JSON logging (e.g., `structlog`). Emit request IDs for traceability. Ship to a log aggregator (ELK, Datadog). |
| **Health checks** | Add `/health` and `/readiness` endpoints for orchestrator probes. |
| **CORS** | Already fixed — origins are now configurable via env vars instead of wildcard `*`. |
| **Input validation** | `recipe_id` references and duplicate day/slot assignments are validated before writes. Before production, add request size limits and a shared error schema. |
| **Error handling** | Global exception handler returning consistent error shapes. Don't leak stack traces. |
| **Testing** | Add integration tests against a real PostgreSQL instance (not just SQLite). Add load tests. |
| **CI/CD** | Automated test pipeline, linting (`ruff`), type checking (`mypy`), and Docker image scanning. |
| **Monitoring** | Prometheus metrics, Grafana dashboards, alerting on error rates and latency P99. |
