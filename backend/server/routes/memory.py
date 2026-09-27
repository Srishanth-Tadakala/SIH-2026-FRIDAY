"""Cognitive Memory & Knowledge Retrieval API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides endpoints for:
- Querying, filtering, and searching persistent cognitive memories.
- Agent-scoped and station-scoped memory views.
- Recording and retrieving memory retrieval telemetry events.
- Creating new persistent memories from agent insights or operator directives.
- Aggregated real-time memory statistics.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database.models import MemoryRecord, MemoryType
from ..auth import User, UserRole, get_current_user, require_role
from ..state import get_server_state

router = APIRouter(prefix="/api/memory", tags=["Agent & Station Memory"])


class CreateMemoryPayload(BaseModel):
    """Payload for creating a new persistent memory record."""
    title: str = Field(..., min_length=3, description="Headline or title")
    summary: str = Field(default="", description="High-level operational summary")
    content: str = Field(..., min_length=5, description="Detailed context or lessons learned")
    memory_type: MemoryType = Field(default=MemoryType.AGENT)
    agent_role: str = Field(default="ALL", description="Target agent or 'ALL'")
    station_id: str = Field(default="bharati", description="'bharati', 'maitri', or 'all'")
    importance: float = Field(default=0.8, ge=0.0, le=1.0)
    severity: str = Field(default="INFO", description="'INFO', 'WARNING', or 'CRITICAL'")
    source: str = Field(default="OPERATOR_DIRECTIVE")
    tags: list[str] = Field(default_factory=list)
    related_incident_id: str | None = Field(default=None)


class SearchMemoryPayload(BaseModel):
    """Payload for semantic/keyword memory query."""
    query: str = Field(..., description="Query terms or incident context")
    agent_role: str = Field(default="ALL")
    station_id: str = Field(default="bharati")
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


@router.get("")
async def list_memories(
    agent_role: str | None = Query(default=None, description="Filter by agent role (e.g. PLANNING, DIAGNOSTIC)"),
    station_id: str | None = Query(default=None, description="Filter by station ('bharati', 'maitri', 'all')"),
    memory_type: str | None = Query(default=None, description="Filter by type (GLOBAL, STATION, AGENT, INCIDENT, SOP)"),
    severity: str | None = Query(default=None, description="Filter by severity ('INFO', 'WARNING', 'CRITICAL')"),
    query: str | None = Query(default=None, description="Search keyword in title, summary, or content"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """List and filter persistent cognitive memories with keyword search."""
    state = get_server_state()
    if not state.memory_repo._records:
        await state.memory_repo.initialize_baseline_memories()
    memories = await state.memory_repo.list_memories(
        agent_role=agent_role,
        station_id=station_id,
        memory_type=memory_type,
        severity=severity,
        search_query=query,
        limit=limit,
        offset=offset,
    )
    return [m.to_dict() for m in memories]


@router.get("/stats/summary")
async def get_memory_subsystem_stats() -> dict[str, Any]:
    """Retrieve real aggregated metrics, counts, and recent retrieval events for memory subsystem."""
    state = get_server_state()
    if not state.memory_repo._records:
        await state.memory_repo.initialize_baseline_memories()
    return await state.memory_repo.get_memory_stats()


@router.get("/retrievals")
async def get_recent_retrievals(
    limit: int = Query(default=20, ge=1, le=50),
) -> list[dict[str, Any]]:
    """Retrieve chronological stream of agent memory retrieval telemetry events."""
    state = get_server_state()
    return await state.memory_repo.get_recent_retrievals(limit=limit)


@router.get("/{memory_id}")
async def get_memory_detail(memory_id: str) -> dict[str, Any]:
    """Retrieve full details of a specific memory record by ID."""
    state = get_server_state()
    memory = await state.memory_repo.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found.")
    return memory.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: CreateMemoryPayload,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new persistent cognitive memory record (requires OPERATOR role)."""
    state = get_server_state()
    record = MemoryRecord(
        title=payload.title,
        summary=payload.summary or payload.title,
        content=payload.content,
        memory_type=payload.memory_type,
        agent_role=payload.agent_role.upper(),
        station_id=payload.station_id.lower(),
        importance=payload.importance,
        severity=payload.severity.upper(),
        source=payload.source,
        tags=payload.tags,
        related_incident_id=payload.related_incident_id,
        metadata={"created_by": current_user.username, "role": current_user.role.value},
    )
    doc_id = await state.memory_repo.save_memory(record)
    return {
        "status": "SUCCESS",
        "memory_id": record.memory_id,
        "database_id": doc_id,
        "record": record.to_dict(),
    }


@router.post("/search")
async def search_memories(payload: SearchMemoryPayload) -> dict[str, Any]:
    """Perform relevance search against persistent memories and record retrieval telemetry."""
    state = get_server_state()
    memories, event = await state.memory_repo.search_relevant_memories(
        agent_role=payload.agent_role,
        station_id=payload.station_id,
        query_text=payload.query,
        tags=payload.tags,
        limit=payload.limit,
    )
    return {
        "query": payload.query,
        "memories_found": len(memories),
        "retrieval_event": event.to_dict(),
        "memories": [m.to_dict() for m in memories],
    }


# Convenience endpoints for agent-scoped and station-scoped memory queries:

@router.get("/agent/{agent_role}")
async def get_agent_memories(
    agent_role: str,
    station_id: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Retrieve memories scoped specifically to an agent role."""
    state = get_server_state()
    memories = await state.memory_repo.list_memories(
        agent_role=agent_role.upper(),
        station_id=station_id,
        limit=limit,
    )
    return [m.to_dict() for m in memories]


@router.get("/station/{station_id}")
async def get_station_memories(
    station_id: str,
    agent_role: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Retrieve memories scoped specifically to a station ('bharati', 'maitri', or 'all')."""
    state = get_server_state()
    memories = await state.memory_repo.list_memories(
        station_id=station_id.lower(),
        agent_role=agent_role,
        limit=limit,
    )
    return [m.to_dict() for m in memories]
