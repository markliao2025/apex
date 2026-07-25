from pathlib import Path
import runpy
from unittest.mock import MagicMock

from sqlalchemy.sql.elements import TextClause


def test_personal_constellation_backfill_binds_literal_suffix() -> None:
    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "0002_phase0_tenancy.py"
    )
    migration = runpy.run_path(str(migration_path))
    operation_mock = MagicMock()
    migration["upgrade"].__globals__["op"] = operation_mock

    migration["upgrade"]()

    statement = next(
        call.args[0]
        for call in operation_mock.execute.call_args_list
        if "md5" in str(call.args[0])
    )
    assert isinstance(statement, TextClause)
    assert statement.compile().params == {"constellation_suffix": ":default"}
