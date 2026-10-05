# Frontend Architecture & User Interface

## Technology Stack

The F.R.I.D.A.Y. frontend is an operational dashboard built with:
- **Framework**: [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite 8](https://vitejs.dev/) with fast Hot Module Replacement (HMR)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/) with a curated Luminous Scandi-Tech color palette
- **Graph & Topology Visualization**: [@xyflow/react](https://reactflow.dev/) (React Flow)
- **Iconography**: [Lucide React](https://lucide.dev/)
- **Unit & Component Testing**: [Vitest](https://vitest.dev/) + [Testing Library](https://testing-library.com/)
- **Linting**: [Oxlint](https://oxc.rs/docs/guide/usage/linter.html)

---

## Directory Structure

```text
frontend/src/
├── api/                        # Strongly-typed API client services
│   ├── client.ts               # Core HTTP request client, token auth & error handling
│   ├── alerts.ts               # Alert retrieval & acknowledgment API
│   └── memory.ts               # Case-based reasoning (CBR) memory query & creation
├── api.ts                      # Central API facade connecting frontend to FastAPI
├── types.ts                    # Global TypeScript interfaces, schemas & enums
├── App.tsx                     # Main application entry point & view routing
├── App.css                     # Global custom styles & animations
├── index.css                   # Tailwind CSS v4 design tokens & utilities
├── main.tsx                    # React DOM root hydration
├── hooks/
│   └── useTelemetryStream.ts   # WebSocket & polling real-time telemetry custom hook
├── components/
│   ├── TopMissionHeader.tsx    # Fixed top status bar, station selector & crisis badge
│   ├── SidebarNavigation.tsx   # Fixed left navigation drawer with station routing
│   ├── HeroSection.tsx         # Polar radar canvas, climate setpoints & scenario triggers
│   ├── CopilotDrawer.tsx       # Sliding Groq AI copilot drawer with chat history
│   ├── Footer.tsx              # Application footer with version & station coordinates
│   └── views/                  # Primary operational view modules
│       ├── OverviewHomeView.tsx# Command homepage with KPIs, radar & crisis injection
│       ├── StationFleetView.tsx# Dual-station fleet comparison (Bharati & Maitri)
│       ├── DigitalTwinView.tsx # Interactive React Flow topological sensor node map
│       ├── AgentsView.tsx      # Multi-agent deliberation DAG & live inter-agent calls
│       ├── MemoryView.tsx      # Case-based reasoning (CBR) incident knowledge base
│       ├── AnalyticsView.tsx   # Satcom sync status, blackout recovery & wear RCM
│       ├── ActionsView.tsx     # Actuator control panel, pending countdowns & PIN modal
│       ├── agents/             # Specialized agent view subcomponents
│       └── digital-twin/       # Digital twin node & drawer subcomponents
└── test/                       # Frontend unit & integration tests
    ├── auth.test.ts            # Token storage and authentication tests
    ├── telemetry.test.ts       # Telemetry formatting and state calculation tests
    ├── integration.test.ts     # API client request handling and error tests
    └── setup.ts                # JSDOM test environment configuration
```

---

## View Routing & Navigation

F.R.I.D.A.Y. implements a clean, URL-synchronized view router without heavyweight external routing libraries:

| View Name | Route Query / Hash | Description |
| :--- | :--- | :--- |
| **Overview** | `?view=overview` or `/` | Command overview, real-time polar environmental radar, station KPIs, quick crisis scenario triggers. |
| **Fleet Command** | `?view=stations` | Side-by-side operational status comparison of Bharati and Maitri stations. |
| **Digital Twin** | `?view=digital_twin` | Interactive `@xyflow/react` node graph mapping 505 sensors across electrical, thermal, hydraulic, and environmental domains. |
| **Cognitive Agents** | `?view=agents` | Real-time 10-agent deliberation visualizer with live inter-agent communication logs. |
| **Memory Bank** | `?view=memory` | Case-Based Reasoning (CBR) historical incident memory search, similarity scoring, and record creation. |
| **Analytics & Satcom** | `?view=analytics` | Iridium satellite channel emulator metrics, differential delta compression stats, equipment wear lifecycle. |
| **Action Center** | `?view=actions` | Physical actuator status, Tier 2 countdown queue, Tier 3 Station Commander PIN authorization modal. |

---

## Real-Time Telemetry Streaming

The frontend synchronizes with backend state via a dual-channel mechanism:
1. **WebSocket Connection (`/ws/telemetry/{station_id}`)**:
   - Streams live 1 Hz sensor state, alerts, KPI calculations, and active agent hypotheses.
   - Automatically handles reconnection with exponential backoff on network dropouts.
2. **REST Polling Fallback (2500ms Interval)**:
   - Queries `/api/telemetry/{station_id}/snapshot` and `/api/stations` to guarantee telemetry visibility even if WebSockets are blocked by proxies.

---

## Design System & UX Standards

- **Visual Theme**: Luminous Scandi-Tech — clean icy surfaces (`#faf8ff`), deep polar navy typography (`#0d1c2f`), electrical cobalt highlights (`#4648d4`), and warning amber/rose accents.
- **Accessibility**: High-contrast typography, descriptive ARIA attributes, semantic HTML elements, and keyboard navigability.
- **Micro-Interactions**: Ambient particle flows on active edge connections, radar pulse animations, and instant responsive status feedback.
