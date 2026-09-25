"""Global Pytest Fixtures for F.R.I.D.A.Y. test suite.

Ensures tests run in a pristine temporary environment and do not pollute or
depend on persistent local data in data/edge_storage/.
"""

import os
import pytest
from backend.database.connection import DatabaseManager
from backend.agents.framework.groq_brain import GroqBrainEngine


@pytest.fixture(autouse=True)
def isolated_test_storage(tmp_path, monkeypatch):
    """Isolate edge storage to a temporary directory and reset singletons for every test run."""
    monkeypatch.setenv("FRIDAY_EDGE_STORAGE_DIR", str(tmp_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    DatabaseManager.reset_instance()
    GroqBrainEngine.reset_instance()
    yield
    DatabaseManager.reset_instance()
    GroqBrainEngine.reset_instance()
