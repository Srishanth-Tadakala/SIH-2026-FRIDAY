"""F.R.I.D.A.Y. Headless Server Package.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Exports:
- create_app: Application factory creating configured FastAPI app.
- app: Default application instance.
- get_server_state: Access singleton server state.
- reset_server_state: Reset state for tests.
"""

from __future__ import annotations

from .app import app, create_app
from .state import ServerState, get_server_state, reset_server_state

__all__ = [
    "create_app",
    "app",
    "ServerState",
    "get_server_state",
    "reset_server_state",
]
