from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_meal_plan_tables(tmp_path):
    db_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)

    assert {
        "users",
        "recipes",
        "ingredients",
        "meal_plans",
        "meal_plan_entries",
    }.issubset(set(inspector.get_table_names()))

    unique_constraints = inspector.get_unique_constraints("meal_plan_entries")
    assert any(
        set(constraint["column_names"]) == {"meal_plan_id", "day_of_week", "meal_slot"}
        for constraint in unique_constraints
    )
