# Telemetry & Industrial Fieldbus Subsystem

## 505 Sensor Channels Across 4 Operational Pillars

F.R.I.D.A.Y. continuously samples and models **505 distinct physical sensor channels** per Antarctic research station. These channels are distributed across four critical operational pillars:

```text
                                  505 SENSORS / STATION
                                            │
        ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
        │                   │                               │                   │
   140 SENSORS         180 SENSORS                     87 SENSORS          98 SENSORS
┌───────┴───────┐   ┌───────┴───────┐               ┌───────┴───────┐   ┌───────┴───────┐
│    ENERGY     │   │INFRASTRUCTURE │               │  ENVIRONMENT  │   │   LOGISTICS   │
│  & MICROGRID  │   │ & LIFE-SUPPORT│               │   & WEATHER   │   │& FLEET ASSETS │
└───────────────┘   └───────────────┘               └───────────────┘   └───────────────┘
```

### Pillar 1: Energy & Microgrid (140 Sensors)
- **Diesel CHP Generators**: Active power (kW), reactive power (kVAR), engine speed (RPM), oil pressure, coolant temperature, exhaust backpressure, vibration.
- **Microgrid Bus**: 400V 3-phase bus voltage, frequency ($50.00\text{ Hz} \pm 0.2\text{ Hz}$), total harmonic distortion (THD), phase angles.
- **Renewable Generation**: Rooftop solar PV strings, 2-axis solar tracking, wind turbine blade pitch, generator electrical output.
- **Storage Subsystem**: LiFePO4 battery energy storage system (BESS), state of charge (SoC), cell voltage divergence, temperature.

### Pillar 2: Infrastructure & Life Support (180 Sensors)
- **Utilidor Thermal Loop**: Glycol supply and return temperatures, pipe skin thermistors, utilidor conduit ambient temperature, circulation flow rate.
- **Potable Water Production**: Snow melter burner status, melt tank water level, UV disinfection intensity, reverse osmosis (RO) membrane differential pressure.
- **Wastewater & Recycling**: Bioreactor sludge level, aeration dissolved oxygen, effluent turbidity, greywater tank level.
- **HVAC & Module Climate**: Supply and return air temperatures, fresh air damper position, relative humidity, $CO_2$ parts per million, differential filter pressure.
- **Fire & Safety**: Ionization smoke obscuration, optical flame detectors, sprinkler riser pressure, utilidor emergency blast door limit switches.

### Pillar 3: Environmental & Weather (87 Sensors)
- **Surface Weather Station**: Ambient temperature (Pt100 RTDs), 10m cup and ultrasonic anemometer wind speed, wind gust, wind direction.
- **Barometric Pressure**: Atmospheric pressure, 3-hour pressure tendency (early warning indicator for sudden katabatic blizzards).
- **Polar Visibility & Snowdrift**: Optical forward-scatter present weather sensor, blowing snow flux sensors, acoustic snow depth sensor.
- **Solar & Radiation**: Pyranometer global horizontal irradiance (GHI), diffuse solar flux, UV index.

### Pillar 4: Logistics & Fleet Operations (98 Sensors)
- **Bulk Fuel Bladders**: Aviation Turbine Fuel (ATF) / Jet-A1 storage tank level, temperature-compensated density, leak detection sumps.
- **Vehicle Fleet**: PistenBully 300 Polar tracked snow groomers, Toyota Hilux polar-modified 4x4s, Ski-Doo snowmobiles (engine telemetry, fuel level, GPS coordinates).
- **Cold-Chain Food Storage**: $-20^\circ\text{C}$ deep freeze walk-in container temperature, humidity, door-open duration sensors.
- **Waste Management**: Incinerator flue temperature, dry waste compactor hydraulic pressure.

---

## Industrial SCADA & Fieldbus Bridges

In production deployment, field instruments communicate over standard industrial fieldbus protocols. F.R.I.D.A.Y. implements native asynchronous bridges in `backend/sensors/bridges/`:

### 1. Modbus TCP Bridge (`modbus_bridge.py`)
- Interfaces with generator controllers (Woodward AGC-4, Cummins PowerCommand) and substation switchgear.
- Polls holding registers asynchronously, decodes IEEE 754 32-bit floating point and 16-bit scaled integers.
- Provides reverse coil write capability for Tier 1-3 physical actuator commands.

### 2. OPC UA Bridge (`opcua_bridge.py`)
- Connects to station Building Management Systems (Siemens Desigo / Beckhoff TwinCAT).
- Subscribes to MonitoredItems for event-driven updates on HVAC damper positions and pump alarms.

### 3. BACnet/IP Bridge (`bacnet_bridge.py`)
- Integrates building automation modules and environmental monitoring loops.

### 4. MQTT Telemetry Bridge (`mqtt_bridge.py`)
- Ingests low-power sensor arrays, battery monitoring systems, and outdoor meteorological stations.

---

## WebSocket Telemetry Streaming

Client applications stream live telemetry via the multiplexed WebSocket endpoint `/ws/telemetry/{station_id}`:
- **Frame Rate**: Configurable up to 1 Hz.
- **Subscription Channels**: `kpis`, `sensors`, `alerts`, `deliberations`, `satcom`.
- **Selective Filtering**: Clients can filter incoming frames by operational pillar or specific sensor IDs to minimize client-side JSON parsing overhead.
