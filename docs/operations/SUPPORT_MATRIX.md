# Phase 0 support matrix

| Environment / capability | Status |
| --- | --- |
| Local Docker Compose synthetic demo | Supported |
| macOS/Linux local lint, typecheck and unit tests | Supported |
| Offline deterministic fixture replay | Supported |
| Scoped constellation planning | Supported for demonstration |
| Redis-backed durable work queue | Not implemented |
| Multi-worker asynchronous planning | Unsupported |
| Production deployment | Reference configuration only |
| Operational CDM/TLE ingestion | Not implemented |
| Independent Pc calculation | Not implemented |
| Maneuver recommendation or execution | Prohibited in Phase 0 |

The FastAPI `BackgroundTasks` planning path is intentionally single-process and
local-demo only. A process restart can interrupt work. A future production
release must introduce a durable queue, idempotent workers and recovery tests.

The bundled `backend/de421.bsp` is excluded from the source/release boundary
until its exact provenance and redistribution terms are documented. Phase 0
does not need it.
