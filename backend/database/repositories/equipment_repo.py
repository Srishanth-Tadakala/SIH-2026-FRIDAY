"""Equipment Lifecycle & Degradation Memory Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Tracks physical asset health, running hours, crank cycles, vibration baselines,
and predictive maintenance countdowns across all station subsystems.
"""

from __future__ import annotations

from collections import defaultdict
import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import EquipmentLifecycleRecord, generate_utc_now

logger = logging.getLogger("friday.database.equipment")

COLLECTION_NAME = "equipment_lifecycle"


class EquipmentRepository:
    """Repository managing digital twin equipment health and wear memory."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
        # In-memory buffer for runtime accumulation: (equipment_id, station_id) -> accumulated_seconds
        self._runtime_buffer: dict[tuple[str, str], float] = defaultdict(float)
        self._flush_threshold_seconds: float = 60.0

    async def initialize_station_assets(self, station_id: str = "bharati") -> None:
        """Seed baseline physical equipment records if not present."""
        count = await self.db.count_records(COLLECTION_NAME, {"station_id": station_id})
        if count > 0:
            return

        baseline_equipment = [
            EquipmentLifecycleRecord(
                equipment_id="chp_1",
                name="CHP Unit 1 (100 kVA Scania Diesel)",
                station_id=station_id,
                subsystem="ENERGY",
                total_running_hours=4210.5,
                total_crank_cycles=342,
                thermal_stress_index=88.4,
                efficiency_health_pct=94.2,
                vibration_rms_mms=3.8,
                next_service_due_hours=4250.0,
                health_status="MAINTENANCE_DUE",
                maintenance_notes="Injector nozzle cleaning & lube oil sample due in 39.5 hours.",
            ),
            EquipmentLifecycleRecord(
                equipment_id="chp_2",
                name="CHP Unit 2 (100 kVA Scania Diesel)",
                station_id=station_id,
                subsystem="ENERGY",
                total_running_hours=2150.0,
                total_crank_cycles=180,
                thermal_stress_index=42.0,
                efficiency_health_pct=98.5,
                vibration_rms_mms=1.8,
                next_service_due_hours=4000.0,
                health_status="OPTIMAL",
                maintenance_notes="Nominal baseline standby unit.",
            ),
            EquipmentLifecycleRecord(
                equipment_id="chp_3",
                name="CHP Unit 3 (100 kVA Scania Diesel - Cold Standby)",
                station_id=station_id,
                subsystem="ENERGY",
                total_running_hours=890.0,
                total_crank_cycles=65,
                thermal_stress_index=15.0,
                efficiency_health_pct=99.8,
                vibration_rms_mms=1.2,
                next_service_due_hours=4000.0,
                health_status="OPTIMAL",
                maintenance_notes="Cold standby reserve. Exercised monthly.",
            ),
            EquipmentLifecycleRecord(
                equipment_id="utilidor_water_line",
                name="Priyadarshini Utilidor Water Trace Line",
                station_id=station_id,
                subsystem="INFRASTRUCTURE",
                total_running_hours=8760.0,
                total_crank_cycles=120,
                thermal_stress_index=92.1,
                efficiency_health_pct=91.0,
                vibration_rms_mms=0.5,
                next_service_due_hours=10000.0,
                health_status="ADVISORY",
                maintenance_notes="Thermal insulation degraded along sector 4 under katabatic cross-winds.",
            ),
            EquipmentLifecycleRecord(
                equipment_id="ahu_01",
                name="Air Handling Unit 01 (Habitat Living Quarters)",
                station_id=station_id,
                subsystem="INFRASTRUCTURE",
                total_running_hours=6420.0,
                total_crank_cycles=450,
                thermal_stress_index=55.0,
                efficiency_health_pct=96.2,
                vibration_rms_mms=2.1,
                next_service_due_hours=7500.0,
                health_status="OPTIMAL",
                maintenance_notes="HEPA & particulate filters replaced last quarter.",
            ),
            EquipmentLifecycleRecord(
                equipment_id="bulk_fuel_pump",
                name="Bulk Fuel Farm Main Transfer Pump",
                station_id=station_id,
                subsystem="LOGISTICS",
                total_running_hours=1240.0,
                total_crank_cycles=890,
                thermal_stress_index=38.0,
                efficiency_health_pct=97.5,
                vibration_rms_mms=1.9,
                next_service_due_hours=3000.0,
                health_status="OPTIMAL",
                maintenance_notes="Impeller seals intact. Flow rate calibrated.",
            ),
        ]

        for eq in baseline_equipment:
            await self.db.update_record(
                COLLECTION_NAME,
                {"equipment_id": eq.equipment_id, "station_id": station_id},
                {"$set": eq.to_dict()},
                upsert=True,
            )
        logger.info("Initialized %d baseline equipment lifecycle records for %s.", len(baseline_equipment), station_id)

    async def accumulate_runtime(
        self,
        equipment_id: str,
        station_id: str,
        dt_seconds: float,
        is_running: bool,
        extra_vibration_mms: float = 0.0,
        force_flush: bool = False,
    ) -> bool:
        """Increment running hours and update wear telemetry with batched in-memory buffering."""
        if not is_running:
            return False

        key = (equipment_id, station_id)
        self._runtime_buffer[key] += dt_seconds

        # Commit to persistent storage only when buffer threshold (60s) reached, vibration anomaly reported, or forced
        if (
            self._runtime_buffer[key] >= self._flush_threshold_seconds
            or extra_vibration_mms > 0
            or force_flush
        ):
            return await self._flush_runtime(equipment_id, station_id, extra_vibration_mms)
        return True

    async def _flush_runtime(
        self,
        equipment_id: str,
        station_id: str,
        extra_vibration_mms: float = 0.0,
    ) -> bool:
        """Commit buffered runtime hours to persistent database storage."""
        key = (equipment_id, station_id)
        buffered_sec = self._runtime_buffer.pop(key, 0.0)
        if buffered_sec <= 0.0 and extra_vibration_mms <= 0:
            return True

        hours_delta = buffered_sec / 3600.0
        doc = await self.db.find_one_record(
            COLLECTION_NAME, {"equipment_id": equipment_id, "station_id": station_id}
        )
        if not doc:
            return False

        new_hours = round(doc.get("total_running_hours", 0.0) + hours_delta, 4)
        due_hours = doc.get("next_service_due_hours", 5000.0)
        status = doc.get("health_status", "OPTIMAL")

        if new_hours >= due_hours:
            status = "MAINTENANCE_DUE"
        elif new_hours >= due_hours - 100.0:
            status = "ADVISORY"

        update_data: dict[str, Any] = {
            "$set": {
                "total_running_hours": new_hours,
                "health_status": status,
                "last_updated_utc": generate_utc_now(),
            }
        }
        if extra_vibration_mms > 0:
            update_data["$set"]["vibration_rms_mms"] = round(extra_vibration_mms, 2)

        return await self.db.update_record(
            COLLECTION_NAME,
            {"equipment_id": equipment_id, "station_id": station_id},
            update_data,
        )

    async def flush_all_buffers(self) -> None:
        """Commit all pending in-memory equipment runtime buffers to persistent storage."""
        pending_keys = list(self._runtime_buffer.keys())
        for eq_id, st_id in pending_keys:
            if self._runtime_buffer.get((eq_id, st_id), 0.0) > 0.0:
                await self._flush_runtime(eq_id, st_id)

    async def get_all_equipment(
        self, station_id: str = "bharati"
    ) -> list[EquipmentLifecycleRecord]:
        """Retrieve all equipment health and wear records for a station."""
        for (eq_id, st_id) in list(self._runtime_buffer.keys()):
            if st_id == station_id and self._runtime_buffer.get((eq_id, st_id), 0.0) > 0.0:
                await self._flush_runtime(eq_id, st_id)

        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict={"station_id": station_id},
            sort_by="health_status",
            sort_order=-1,
            limit=50,
        )
        results: list[EquipmentLifecycleRecord] = []
        for d in raw_docs:
            try:
                results.append(EquipmentLifecycleRecord(**d))
            except Exception:
                pass
        return results

    async def get_all_assets(
        self, station_id: str = "bharati"
    ) -> list[EquipmentLifecycleRecord]:
        """Alias for get_all_equipment."""
        return await self.get_all_equipment(station_id)

    async def get_asset(
        self, equipment_id: str, station_id: str = "bharati"
    ) -> EquipmentLifecycleRecord | None:
        """Retrieve a specific asset record by equipment_id and station_id."""
        key = (equipment_id, station_id)
        if self._runtime_buffer.get(key, 0.0) > 0.0:
            await self._flush_runtime(equipment_id, station_id)

        doc = await self.db.find_one_record(
            COLLECTION_NAME, {"equipment_id": equipment_id, "station_id": station_id}
        )
        if doc:
            try:
                return EquipmentLifecycleRecord(**doc)
            except Exception:
                pass
        return None
