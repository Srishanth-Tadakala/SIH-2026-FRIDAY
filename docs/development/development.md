# Developer Workflow & Extensibility Guide

This document describes how to extend and develop new capabilities within the F.R.I.D.A.Y. platform.

---

## 1. Extending the Digital Twin Engine

The deterministic digital twin is defined in `backend/core/engine.py`.

### Adding a New Physical Sensor Point
1. Define the physical channel schema and engineering units in `backend/sensors/bharati_sensors/` under the appropriate operational pillar (`energy`, `infrastructure`, `environment`, `logistics`).
2. Add the nominal calibration range and warning/critical alarm thresholds.
3. In `backend/core/engine.py`, instantiate the sensor during engine initialization.
4. Add physics update equations in `_compute_thermodynamics()` or `_compute_microgrid()`:
   ```python
   # Example: Battery thermal dissipation
   temp_delta = (current_amps ** 2 * internal_resistance_ohms) / thermal_mass
   self.battery_temp_c += temp_delta * dt_seconds
   ```
5. Add corresponding test cases in `tests/sensors/bharati/`.

---

## 2. Implementing a New Specialized Cognitive Agent

All cognitive agents inherit from `BaseAgent` in `backend/agents/framework/base_agent.py`.

### Step-by-Step Agent Implementation
1. Create a new module in `backend/agents/specialized/`:
   ```python
   from backend.agents.framework.base_agent import BaseAgent
   from backend.agents.framework.models import AgentMessage, MessageType

   class CryosphereSafetyAgent(BaseAgent):
       def __init__(self, bus, brain=None):
           super().__init__(
               agent_id="agent_cryosphere",
               name="Cryosphere Glacier Ice Safety Agent",
               role="Crevasse and ice-shelf movement monitoring",
               bus=bus,
               brain=brain,
           )

       async def process_message(self, message: AgentMessage) -> None:
           # Listen for seismic or GPS drift sensor updates
           if message.topic == "sensors.environment":
               await self._evaluate_crevasse_risk(message.payload)
   ```
2. Register the agent in `backend/server/state.py` within `_init_cognitive_society()`.
3. Add a dedicated test file in `tests/agents/test_agent_cryosphere.py`.
4. Update the React Flow visualizer nodes in `frontend/src/components/views/AgentsView.tsx`.

---

## 3. Working with SCADA & Industrial Bridges

Fieldbus bridges in `backend/sensors/bridges/` allow real or simulated PLCs to stream data directly into the twin engine:
- To test against a virtual Modbus PLC:
  ```bash
  python tools/virtual_modbus_server.py
  ```
- To test against a virtual OPC UA server:
  ```bash
  python tools/virtual_opcua_server.py
  ```
- To run simulated field PLC state transitions:
  ```bash
  python tools/simulate_field_plc.py
  ```

---

## 4. Code Style & Quality Standards

- **Python**: Format code cleanly, adhere to PEP 8, and use explicit type hints throughout (`from __future__ import annotations`).
  Verify code quality:
  ```bash
  python -m ruff check backend/ tests/ --select E9,F63,F7,F82
  ```
- **TypeScript**: Use strict type definitions (avoid `any` where possible) and avoid unused imports.
  Lint frontend:
  ```bash
  cd frontend && npm run lint
  ```
