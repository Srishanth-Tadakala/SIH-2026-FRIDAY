"""State Synchronization and Operator Session API Endpoints.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Ensures that the entire platform (active station, active tab, autonomous mode,
copilot conversation history, and operator identity) is persisted across
logins, browser tabs, and page refreshes without starting fresh.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...database.models import OperatorAuditRecord, StationStateSyncRecord, generate_utc_now
from ..state import get_server_state

logger = logging.getLogger("friday.server.routes.sync")

router = APIRouter(prefix="/api/sync", tags=["State Synchronization & Session Management"])


class SyncUpdateRequest(BaseModel):
    station_id: str | None = None
    active_tab: str | None = None
    autonomous_mode: bool | None = None
    voice_enabled: bool | None = None
    cognitive_category: str | None = None
    pillar_filter: str | None = None
    operator_id: str | None = None
    operator_name: str | None = None
    active_scenario: str | None = None
    authenticated: bool | None = None
    preferences: dict[str, Any] | None = None


class LoginRequest(BaseModel):
    operator_id: str = Field(default="STATION_COMMANDER")
    operator_name: str = Field(default="Cmdr. T. Srishanth")
    pin: str | None = Field(default=None, description="Station Security Passcode or PIN")
    passcode: str | None = Field(default=None, description="Station Security Passcode or PIN")
    station_id: str = Field(default="bharati")


@router.get("/state")
async def get_synchronized_state() -> dict[str, Any]:
    """Retrieve complete synchronized platform state package for client hydration."""
    state = get_server_state()

    # Load persistent state from repository if available
    record = await state.state_sync_repo.get_state()
    if not record:
        record = StationStateSyncRecord(
            station_id=state.active_station_id,
            operator_id="STATION_COMMANDER",
            operator_name="Cmdr. T. Srishanth",
            authenticated=True,
            active_tab="topo",
            autonomous_mode=state.autonomous_mode_enabled,
            voice_enabled=True,
        )
        await state.state_sync_repo.save_state(record)

    copilot_count = await state.copilot_repo.count_messages(station_id=state.active_station_id)
    db_status = state.db_manager.get_status()
    engine = state.get_engine(state.active_station_id)
    sc = getattr(engine.active_scenario, "value", str(engine.active_scenario))

    return {
        "status": "SUCCESS",
        "sync_id": record.sync_id,
        "station_id": state.active_station_id,
        "active_station": state.active_station_id,
        "operator_id": record.operator_id,
        "operator_name": record.operator_name,
        "authenticated": record.authenticated,
        "operator": {
            "operator_id": record.operator_id,
            "operator_name": record.operator_name,
            "authenticated": record.authenticated,
            "callsign": f"ANTARCTIC-{record.operator_id[:8]}",
        },
        "active_tab": record.active_tab,
        "autonomous_mode": record.autonomous_mode,
        "voice_enabled": record.voice_enabled,
        "cognitive_category": record.cognitive_category,
        "pillar_filter": record.pillar_filter,
        "active_scenario": record.active_scenario or sc,
        "preferences": record.preferences,
        "copilot_history_count": copilot_count,
        "database_status": db_status,
        "last_synced_utc": record.last_synced_utc,
        "server_time": time.time(),
    }


@router.post("/state")
async def update_synchronized_state(req: SyncUpdateRequest) -> dict[str, Any]:
    """Update and persist client state changes to local edge database."""
    state = get_server_state()

    record = await state.state_sync_repo.get_state()
    if not record:
        record = StationStateSyncRecord()

    if req.station_id and req.station_id in state.stations:
        state.active_station_id = req.station_id
        record.station_id = req.station_id

    if req.active_tab is not None:
        record.active_tab = req.active_tab

    if req.autonomous_mode is not None:
        record.autonomous_mode = req.autonomous_mode
        state.is_continuous_loop_running = req.autonomous_mode

    if req.voice_enabled is not None:
        record.voice_enabled = req.voice_enabled

    if req.cognitive_category is not None:
        record.cognitive_category = req.cognitive_category

    if req.pillar_filter is not None:
        record.pillar_filter = req.pillar_filter

    if req.active_scenario is not None:
        record.active_scenario = req.active_scenario

    if req.operator_id is not None:
        record.operator_id = req.operator_id

    if req.operator_name is not None:
        record.operator_name = req.operator_name

    if req.authenticated is not None:
        record.authenticated = req.authenticated

    if req.preferences is not None:
        record.preferences.update(req.preferences)

    record.last_synced_utc = generate_utc_now()
    record.last_synced_unix = time.time()

    await state.state_sync_repo.save_state(record)

    return {
        "status": "SUCCESS",
        "message": "Platform state successfully synchronized and persisted.",
        "state": record.to_dict(),
    }


@router.post("/login")
async def operator_login(req: LoginRequest) -> dict[str, Any]:
    """Authenticate station operator and restore personal session continuity."""
    state = get_server_state()

    # Valid passcodes: Commander PIN "BHARATI-CMD-2026", "MAITRI-CMD-2026", or standard "ANTARCTIC-2026"
    valid_pins = {"BHARATI-CMD-2026", "MAITRI-CMD-2026", "ANTARCTIC-2026", "FRIDAY-ADMIN-2026"}
    raw_pass = req.pin or req.passcode or ""
    clean_pass = raw_pass.strip().upper()

    if not clean_pass or clean_pass not in valid_pins:
        # Audit failed login attempt
        fail_audit = OperatorAuditRecord(
            station_id=req.station_id,
            operator_id=req.operator_id,
            action_type="LOGIN_FAILED_INVALID_CREDENTIALS",
            details=f"Invalid authentication attempt for {req.operator_name}",
            authorized=False,
        )
        await state.audit_repo.log_audit(fail_audit)
        return JSONResponse(
            status_code=401,
            content={
                "status": "UNAUTHORIZED",
                "authenticated": False,
                "detail": "Authentication failed. Invalid Commander PIN or Passcode.",
                "message": "Authentication failed. Invalid Commander PIN or Passcode.",
            }
        )

    # Successful login: audit action
    success_audit = OperatorAuditRecord(
        station_id=req.station_id,
        operator_id=req.operator_id,
        action_type="OPERATOR_LOGIN_AUTHENTICATED",
        details=f"Authenticated session established for {req.operator_name}",
        authorized=True,
    )
    await state.audit_repo.log_audit(success_audit)

    # Persist session state
    record = await state.state_sync_repo.get_state()
    if not record:
        record = StationStateSyncRecord()

    record.station_id = req.station_id
    record.operator_id = req.operator_id
    record.operator_name = req.operator_name
    record.authenticated = True
    record.last_synced_utc = generate_utc_now()
    record.last_synced_unix = time.time()

    if req.station_id in state.stations:
        state.active_station_id = req.station_id

    await state.state_sync_repo.save_state(record)

    token = f"POLAR-TOKEN-{clean_pass[:8]}-{int(time.time())}"

    return {
        "status": "SUCCESS",
        "authenticated": True,
        "token": token,
        "message": f"Welcome back, {req.operator_name}. Operational state restored from Edge Database.",
        "station_id": req.station_id,
        "operator_name": req.operator_name,
        "operator": {
            "operator_id": record.operator_id,
            "operator_name": record.operator_name,
            "authenticated": True,
            "role": "STATION_COMMANDER" if "CMD" in clean_pass else "SYSTEMS_ENGINEER",
        },
        "active_tab": record.active_tab,
        "autonomous_mode": state.is_continuous_loop_running,
    }


@router.post("/logout")
async def operator_logout() -> dict[str, Any]:
    """Log out current operator and return to monitoring session."""
    state = get_server_state()

    record = await state.state_sync_repo.get_state()
    if record:
        audit = OperatorAuditRecord(
            station_id=state.active_station_id,
            operator_id=record.operator_id,
            action_type="OPERATOR_LOGOUT",
            details=f"Operator {record.operator_name} logged out.",
            authorized=True,
        )
        await state.audit_repo.log_audit(audit)

        record.operator_id = "MONITORING_OPERATOR"
        record.operator_name = "Polar Watchstander"
        record.authenticated = False
        await state.state_sync_repo.save_state(record)

    return {
        "status": "SUCCESS",
        "authenticated": False,
        "message": "Operator logged out. System in continuous autonomous monitoring mode.",
    }


@router.post("/full_refresh")
async def full_platform_refresh() -> dict[str, Any]:
    """Force complete synchronization between edge database, satcom queue, and server state."""
    state = get_server_state()
    synced_count = await state.db_sync_worker.sync_pending_batches()
    record = await state.state_sync_repo.get_state()

    return {
        "status": "SYNCHRONIZED",
        "twin_status": "ONLINE",
        "database": state.db_manager.get_status(),
        "synced_state": record.to_dict() if record else {},
        "synced_batches": synced_count,
        "active_station": state.active_station_id,
        "server_time": time.time(),
        "message": "Complete system state refreshed and synchronized across all subsystems.",
    }
