"""Global Pytest Fixtures for F.R.I.D.A.Y. test suite.

Ensures tests run in a pristine temporary environment and do not pollute or
depend on persistent local data in data/edge_storage/.
"""

import os
import pytest
from backend.database.connection import DatabaseManager


@pytest.fixture(autouse=True)
def isolated_test_storage(tmp_path, monkeypatch):
    """Isolate edge storage to a temporary directory for every test run."""
    monkeypatch.setenv("FRIDAY_EDGE_STORAGE_DIR", str(tmp_path))
    # Reset singleton DatabaseManager so it uses the temporary path
    DatabaseManager.reset_instance()
    yield
    DatabaseManager.reset_instance()
