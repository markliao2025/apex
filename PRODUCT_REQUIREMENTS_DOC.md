# Apex + Rigor — Product Requirements Document (PRD)

> **Version:** 1.0
> **Date:** 2026-06-13
> **Audience:** AI Coding Agent (LLM-based developer)
> **Goal:** Complete, unambiguous specification for building MVP1 (single-satellite task planning AI Native agent) and MVP2 (orbital AI robustness evaluation Space Tech platform).
>
> **Critical Rule for AI Agent Reader:**
> - Every requirement is tagged with **MUST / SHOULD / MAY** per RFC 2119
> - Every data structure has a complete JSON schema example
> - Every API has request/response examples
> - Every UI screen has component hierarchy
> - When you encounter a section labeled **[TODO: AGENT DECISION]**, you MUST design the implementation yourself and document your design choices before coding
> - Do NOT skip sections. Build EVERYTHING described in this document.

---

## TABLE OF CONTENTS

1. [Product Overview](#1-product-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Data Model (Complete Schema)](#3-data-model-complete-schema)
4. [Product 1: Apex — Satellite Task Planning Agent](#4-product-1-apex-satellite-task-planning-agent)
5. [Product 2: Rigor — Orbital AI Robustness Evaluation](#5-product-2-rigor-orbital-ai-robustness-evaluation)
6. [API Specification](#6-api-specification)
7. [Frontend Specification](#7-frontend-specification)
8. [Implementation Order for AI Agent](#8-implementation-order-for-ai-agent)

---

## 1. PRODUCT OVERVIEW

### 1.1 Product Names and Definitions

| Name | Type | What It Does |
|------|------|-------------|
| **Apex** | AI Native Platform | Natural-language satellite task planning AI Native agent that generates physically-feasible observation/communication schedules for single or multi-satellite constellations |
| **Rigor** | Space Tech Platform | Automated robustness evaluation engine that tests AI models against orbital degradation scenarios (cloud cover, illumination changes, sensor noise, attitude jitter, radiation effects) |

### 1.2 MVP Scope

| MVP | Product | Scope | Timeline |
|-----|---------|-------|----------|
| **MVP1** | Apex | Single-satellite task planning. Natural language input → task list → SGP4 orbit computation → feasible schedule. Web UI | Months 1-3 |
| **MVP2** | Rigor | Core evaluation engine. Support optical remote sensing models. 5 degradation types. Basic scoring report | Months 1-3 |

Both MVPs ship on the same codebase under one AI Native + Space Tech platform.

### 1.3 Non-Goals (Out of Scope for MVP)

- Multi-satellite constellation planning (Phase 2)
- Multi-ground station coordination (Phase 2)
- SAR model support (Phase 2)
- Compliance certification (Phase 3)
- Private deployment / on-premise (Phase 3)
- Real satellite telemetry integration (Phase 2)

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Tech Stack

```
Frontend:     React 18 + TypeScript + TailwindCSS + shadcn/ui
Backend:      FastAPI (Python 3.11) + PostgreSQL 15 + Redis 7
LLM Layer:    OpenAI API (gpt-4o) + LangChain for orchestration
Orbit Engine: skyfield (Python) + sgp4 (Python)
Scheduler:    OR-Tools CP-SAT solver (Google)
Testing:      pytest + playwright (E2E)
Infra:        Docker + Docker Compose (local) / Railway (deploy)
```

### 2.2 System Components

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                   │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │Chat UI   │  │Schedule   │  │Evaluation        │  │
│  │(Orbital) │  │Viewer     │  │Dashboard         │  │
│  │          │  │(Gantt Chart│  │(Rigor)      │  │
│  │          │  │ + Map)     │  │                  │  │
│  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
└───────┼───────────────┼────────────────┼────────────┘
        │               │                │
        ▼               ▼                ▼
┌─────────────────────────────────────────────────────┐
│                   API Gateway (FastAPI)               │
│  /api/v1/auth  /api/v1/planning  /api/v1/eval       │
└───────┬───────────────┬────────────────┬────────────┘
        │               │                │
   ┌────┴────┐    ┌─────┴──────┐   ┌────┴─────┐
   │Planning │    │Orbit Engine│   │Evaluator │
   │Service  │    │(SGP4 +     │   │Engine   │
   │(Agent)  │    │  skyfield) │   │(Degrad.)│
   └────┬────┘    └─────┬──────┘   └────┬─────┘
        │               │                │
   ┌────┴───────────────┴────────────────┴────┐
   │          PostgreSQL + Redis               │
   └──────────────────────────────────────────┘
```

### 2.3 Agent Workflow Architecture (Apex)

```
User Natural Language Input
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Parser (OpenAI gpt-4o via     │
│  LangChain)                         │
│                                     │
│  Input: "Next week, image all       │
│  flood zones in Southeast Asia,     │
│  resolution better than 5m"         │
│                                     │
│  Output (JSON):                      │
│  {                                  │
│    "region": ["Southeast Asia"],     │
│    "event": "flood",                 │
│    "resolution_m": 5,                │
│    "time_window": "7d",              │
│    "priority": "normal"              │
│  }                                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Satellite Inventory Lookup         │
│  - Get all satellites with EO       │
│    payload < 5m resolution          │
│  - Get their current TLE from       │
│    CelesTrak API                     │
│  - Calculate overpass windows for   │
│    target region                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Constraint Solver (OR-Tools        │
│  CP-SAT)                            │
│                                     │
│  Decision variables:                │
│  x[satellite, time_slot] = 0 or 1  │
│                                     │
│  Constraints:                       │
│  1. Each request satisfied <= 1 time│
│  2. Satellite cannot image two      │
│     regions simultaneously          │
│  3. Battery must not deplete        │
│  4. Storage must not overflow       │
│  5. Min turn rate between targets   │
│                                     │
│  Objective: Maximize total covered  │
│  request priority                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Schedule Validator                 │
│  - Verify each task is physically   │
│    feasible (elevation angle,       │
│    illumination, contact window)    │
│  - If invalid, return to solver     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Output                             │
│  - Structured schedule (JSON)       │
│  - Gantt chart data (frontend)      │
│  - Map visualization data (frontend)│
└─────────────────────────────────────┘
```

**[CRITICAL ARCHITECTURAL RULE]** The LLM NEVER generates the schedule directly. The LLM ONLY parses natural language into structured constraints. The actual schedule is ALWAYS produced by the OR-Tools CP-SAT solver, then validated by physics checks. This prevents hallucinated schedules.

---

## 3. DATA MODEL (COMPLETE SCHEMA)

### 3.1 User

```json
{
  "id": "uuid",
  "email": "string (unique, email format)",
  "password_hash": "string (bcrypt, 60 chars)",
  "name": "string (max 100 chars)",
  "plan": "free | starter | pro | enterprise",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### 3.2 Satellite

```json
{
  "id": "uuid",
  "norad_id": "int (from CelesTrak)",
  "name": "string (max 200 chars)",
  "tle_line1": "string (70 chars, TLE Line 1)",
  "tle_line2": "string (70 chars, TLE Line 2)",
  "tle_epoch": "ISO 8601 timestamp",
  "orbit_type": "leo | meo | geo | sso",
  "altitude_km_min": "float (minimum altitude)",
  "altitude_km_max": "float (maximum altitude)",
  "inclination_deg": "float (0-180)",
  "eccentricity": "float (0-1)",
  "payload_type": "eo_optical | eo_multispectral | sar | comms",
  "max_resolution_m": "float (ground resolution in meters)",
  "swath_width_km": "float (image swath width)",
  "max_storage_gb": "float (onboard storage)",
  "max_power_w": "float (maximum power draw)",
  "min_elevation_deg": "float (minimum imaging elevation, default 5.0)",
  "turn_rate_deg_s": "float (max turn rate, default 2.0)",
  "ground_stations": ["string (ground station IDs)"],
  "owner_company_id": "uuid (nullable, linked to customer)",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### 3.3 GroundStation

```json
{
  "id": "uuid",
  "name": "string (max 200 chars)",
  "latitude": "float (-90 to 90)",
  "longitude": "float (-180 to 180)",
  "altitude_m": "float (above sea level)",
  "min_elevation_deg": "float (default 5.0)",
  "band": "s_band | c_band | x_band | ku_band",
  "antenna_diameter_m": "float",
  "created_at": "ISO 8601 timestamp"
}
```

### 3.4 PlanningRequest (User's Natural Language Request)

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "raw_input": "string (original natural language text)",
  "parsed_intent": {
    "target_region": "string (geo-description, e.g. 'Southeast Asia')",
    "event_filter": "string (optional, e.g. 'flood')",
    "resolution_requirement_m": "float (max ground resolution)",
    "time_window_days": "int (planning horizon)",
    "priority": "low | normal | high | urgent",
    "sensor_preference": "string (optional, e.g. 'multispectral')",
    "exclusion_zones": ["string (optional geo-descriptions)"]
  },
  "status": "pending | planning | planning_error | ready | deployed",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### 3.5 PlannedTask

```json
{
  "id": "uuid",
  "planning_request_id": "uuid",
  "satellite_id": "uuid",
  "ground_station_id": "uuid (nullable, for downlink)",
  "target_area": {
    "type": "Polygon",
    "coordinates": "[[lng, lat], [lng, lat], ...]"
  },
  "event_window": {
    "aos_time": "ISO 8601 (Acquisition of Signal)",
    "los_time": "ISO 8601 (Loss of Signal)",
    "max_elevation_deg": "float"
  },
  "resource_allocation": {
    "power_w": "float (expected power consumption)",
    "storage_mb": "float (expected data size)",
    "battery_delta_percent": "float"
  },
  "solver_status": "optimal | suboptimal | infeasible",
  "validator_status": "passed | failed | pending",
  "failure_reason": "string (nullable, if validator_status=failed)",
  "priority_score": "float (0-1, computed from input priority)",
  "created_at": "ISO 8601 timestamp"
}
```

### 3.6 EvaluationJob (Rigor)

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "model_name": "string (user-provided model name)",
  "model_type": "classification | detection | segmentation",
  "sensor_type": "optical | multispectral | hyperspectral",
  "model_artifact": "string (S3 path or local path to model file .onnx/.pt/.pb)",
  "baseline_dataset": {
    "dataset_id": "uuid",
    "num_images": "int"
  },
  "degradation_types_enabled": ["cloud | illumination | noise | jitter | radiation"],
  "status": "pending | running | completed | failed",
  "progress_percent": "int (0-100)",
  "created_at": "ISO 8601 timestamp",
  "completed_at": "ISO 8601 timestamp (nullable)"
}
```

### 3.7 EvaluationResult

```json
{
  "id": "uuid",
  "evaluation_job_id": "uuid",
  "degradation_type": "cloud | illumination | noise | jitter | radiation",
  "severity_level": "none | light | moderate | severe | critical",
  "metrics": {
    "accuracy_clean": "float (0-1, on undegraded data)",
    "accuracy_degraded": "float (0-1, on degraded data)",
    "accuracy_drop_pct": "float (percentage point drop)",
    "f1_score_clean": "float (0-1)",
    "f1_score_degraded": "float (0-1)",
    "mAP_clean": "float (0-1, for detection models)",
    "mAP_degraded": "float (0-1, for detection models)",
    "samples_tested": "int",
    "samples_passed": "int (above threshold)"
  },
  "robustness_score": "float (0-100, composite score)",
  "recommendation": "string (human-readable, e.g. 'Model loses >30% accuracy under moderate cloud cover. Not recommended for deployment in tropical regions.')",
  "generated_at": "ISO 8601 timestamp"
}
```

### 3.8 Database Migration (SQLAlchemy Models)

```python
# core/models.py - Full SQLAlchemy model definitions

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
import uuid

Base = declarative_base()

class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class OrbitType(str, enum.Enum):
    LEO = "leo"
    MEO = "meo"
    GEO = "geo"
    SSO = "sso"

class PayloadType(str, enum.Enum):
    EO_OPTICAL = "eo_optical"
    EO_MULTISPECTRAL = "eo_multispectral"
    SAR = "sar"
    COMMS = "comms"

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    PLANNING_ERROR = "planning_error"
    READY = "ready"
    DEPLOYED = "deployed"

class SolverStatus(str, enum.Enum):
    OPTIMAL = "optimal"
    SUBOPTIMAL = "suboptimal"
    INFEASIBLE = "infeasible"

class ValidatorStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"

class DegradationType(str, enum.Enum):
    CLOUD = "cloud"
    ILLUMINATION = "illumination"
    NOISE = "noise"
    JITTER = "jitter"
    RADIATION = "radiation"

class ModelType(str, enum.Enum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"

class SeverityLevel(str, enum.Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(100), nullable=True)
    plan = Column(Enum(PlanType), default=PlanType.FREE, nullable=False)
    created_at = Column(DateTime, server_default="NOW()")
    updated_at = Column(DateTime, server_default="NOW()", onupdate="NOW()")
    planning_requests = relationship("PlanningRequest", back_populates="user")
    evaluation_jobs = relationship("EvaluationJob", back_populates="user")

class Satellite(Base):
    __tablename__ = "satellites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norad_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tle_line1 = Column(String(70), nullable=False)
    tle_line2 = Column(String(70), nullable=False)
    tle_epoch = Column(DateTime, nullable=False)
    orbit_type = Column(Enum(OrbitType), nullable=False)
    altitude_km_min = Column(Float, nullable=False)
    altitude_km_max = Column(Float, nullable=False)
    inclination_deg = Column(Float, nullable=False)
    eccentricity = Column(Float, nullable=False)
    payload_type = Column(Enum(PayloadType), nullable=False)
    max_resolution_m = Column(Float, nullable=False)
    swath_width_km = Column(Float, nullable=False)
    max_storage_gb = Column(Float, nullable=False)
    max_power_w = Column(Float, nullable=False)
    min_elevation_deg = Column(Float, default=5.0)
    turn_rate_deg_s = Column(Float, default=2.0)
    created_at = Column(DateTime, server_default="NOW()")
    updated_at = Column(DateTime, server_default="NOW()", onupdate="NOW()")

class GroundStation(Base):
    __tablename__ = "ground_stations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=False)
    min_elevation_deg = Column(Float, default=5.0)
    band = Column(String(20), nullable=False)
    antenna_diameter_m = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default="NOW()")

class PlanningRequest(Base):
    __tablename__ = "planning_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    raw_input = Column(Text, nullable=False)
    parsed_intent = Column(JSON, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default="NOW()")
    updated_at = Column(DateTime, server_default="NOW()", onupdate="NOW()")
    user = relationship("User", back_populates="planning_requests")
    tasks = relationship("PlannedTask", back_populates="request")

class PlannedTask(Base):
    __tablename__ = "planned_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    planning_request_id = Column(UUID(as_uuid=True), ForeignKey("planning_requests.id"), nullable=False)
    satellite_id = Column(UUID(as_uuid=True), ForeignKey("satellites.id"), nullable=False)
    ground_station_id = Column(UUID(as_uuid=True), ForeignKey("ground_stations.id"), nullable=True)
    target_area = Column(JSON, nullable=False)
    event_window = Column(JSON, nullable=False)
    resource_allocation = Column(JSON, nullable=False)
    solver_status = Column(Enum(SolverStatus), default=SolverStatus.OPTIMAL)
    validator_status = Column(Enum(ValidatorStatus), default=ValidatorStatus.PENDING)
    failure_reason = Column(Text, nullable=True)
    priority_score = Column(Float, default=0.5)
    created_at = Column(DateTime, server_default="NOW()")
    request = relationship("PlanningRequest", back_populates="tasks")
    satellite = relationship("Satellite")
    ground_station = relationship("GroundStation")

class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_name = Column(String(200), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    model_artifact_path = Column(String(500), nullable=False)
    baseline_dataset_id = Column(UUID(as_uuid=True), nullable=True)
    num_baseline_images = Column(Integer, default=0)
    degradation_types_enabled = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    progress_percent = Column(Integer, default=0)
    created_at = Column(DateTime, server_default="NOW()")
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="evaluation_jobs")
    results = relationship("EvaluationResult", back_populates="job")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_job_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_jobs.id"), nullable=False)
    degradation_type = Column(Enum(DegradationType), nullable=False)
    severity_level = Column(Enum(SeverityLevel), nullable=False)
    metrics = Column(JSON, nullable=False)
    robustness_score = Column(Float, nullable=False)
    recommendation = Column(Text, nullable=False)
    generated_at = Column(DateTime, server_default="NOW()")
    job = relationship("EvaluationJob", back_populates="results")
```

---

## 4. PRODUCT 1: APEX — SATELLITE TASK PLANNING AGENT

### 4.1 User Stories

**US-1: Natural Language Task Entry**
- AS A satellite operations manager
- I WANT to type "Image Tokyo Bay next 48 hours at resolution better than 3m"
- SO THAT I can quickly create a task without filling complex forms
- GIVEN I am logged in
- WHEN I type a request and press "Generate Schedule"
- THEN the system shows:
  - Parsed intent summary (region, resolution, time window, priority)
  - Confidence score for each parsed field
  - "Edit" buttons on low-confidence fields
  - "Confirm and Plan" button

**US-2: Schedule Generation**
- AS A satellite operations manager
- I WANT a feasible schedule generated automatically
- SO THAT I can see which satellites can image the target when
- GIVEN I have confirmed the parsed intent
- WHEN the solver completes
- THEN the schedule displays as:
  - A Gantt chart showing tasks against time
  - A map showing target areas and satellite ground tracks
  - A task list with satellite name, acquisition time, duration, estimated data size
  - Resource usage indicators (battery %, storage %)

**US-3: Schedule Editing**
- AS A satellite operations manager
- I WANT to manually adjust task priorities or swap satellites
- SO THAT I can handle emergencies
- GIVEN I have a generated schedule
- WHEN I drag a task to a different time slot or satellite
- THEN the system validates the change and updates all dependent tasks
- IF the change violates a constraint, show a red error message explaining which constraint

**US-4: Dynamic Replanning (Emergency Mode)**
- AS A disaster response coordinator
- I WANT to re-plan entire constellation when an emergency occurs
- SO THAT priority tasks get scheduled immediately
- GIVEN I have existing scheduled tasks
- WHEN I create an "urgent" task with natural language
- THEN the system inserts the urgent task and pushes lower-priority tasks down
- THEN it shows a diff of what changed

### 4.2 LLM Intent Parsing — Detailed Spec

**Input to LLM:**
```
Natural language text: "{user_input}"
Available satellites: [{
  "norad_id": integer,
  "name": string,
  "payload_type": "eo_optical|eo_multispectral|sar|comms",
  "max_resolution_m": float,
  "altitude_km_min": float,
  "altitude_km_max": float,
  "inclination_deg": float
}]
```

**Output schema (strict JSON, no markdown wrapper):**
```json
{
  "region_description": "string or null",
  "bounding_box": {
    "southwest_lat": float or null,
    "southwest_lng": float or null,
    "northeast_lat": float or null,
    "northeast_lng": float or null
  },
  "event_filter": "string or null",
  "resolution_requirement_m": float or null,
  "time_window_days": int or null,
  "priority": "low|normal|high|urgent",
  "sensor_preference": "string or null",
  "exclusion_zones": ["string or null"],
  "confidence": {
    "region_description": 0.0-1.0,
    "bounding_box": 0.0-1.0,
    "resolution_requirement_m": 0.0-1.0,
    "time_window_days": 0.0-1.0,
    "priority": 0.0-1.0
  },
  "uncertainty_notes": ["string"]
}
```

**[TODO: AGENT DECISION]** Implement the bounding box extraction. Options:
A) LLM extracts lat/lng directly (faster, less accurate for fuzzy descriptions)
B) LLM returns region name, then a separate geocoding service converts to bbox
Recommendation: Use option B with a built-in geocoding map for 200 known world regions, falling back to option A for unknown descriptions. Document your choice.

### 4.3 SGP4 Orbit Propagation — Detailed Spec

**Dependency:** Use `skyfield` Python library for TLE loading and propagation, `sgp4` library for propagation engine.

**Function signature:**
```python
def calculate_overpass_windows(
    satellite: Satellite,
    ground_station: GroundStation,
    start_time: datetime,
    end_time: datetime,
    min_elevation_deg: float = 5.0
) -> list[OverpassWindow]:
    """
    Returns list of ground station visibility windows for the satellite.
    Each window: {aos, los, max_elevation, duration_seconds}
    """
```

**Function signature:**
```python
def calculate_imaging_windows(
    satellite: Satellite,
    target_bbox: BoundingBox,
    start_time: datetime,
    end_time: datetime,
    min_elevation_deg: float = 5.0,
    max_sun_angle_deg: float = 60.0  # max solar zenith angle for illumination
) -> list[ImagingWindow]:
    """
    Returns list of times when satellite can image the target area.
    Each window: {aos, los, max_elevation, illumination_pct, duration_seconds}
    illumination_pct: 0.0-1.0 (fraction of target area that is sunlit)
    """
```

**Expected input for test:**
```python
satellite = Satellite(
    norad_id=25544,  # ISS
    tle_line1="1 25544U ...",
    tle_line2="2 25544U ...",
    max_resolution_m=0.5,
    swath_width_km=15.0
)
target_bbox = BoundingBox(southwest_lat=35.5, southwest_lng=139.5, northeast_lat=35.9, northeast_lng=140.1)
```

**Expected output format:**
```python
[
    ImagingWindow(
        aos=datetime(2026, 6, 14, 8, 23, 15),
        los=datetime(2026, 6, 14, 8, 23, 45),
        max_elevation=72.5,
        illumination_pct=0.85,
        duration_seconds=30
    ),
    # ... more windows
]
```

### 4.4 OR-Tools CP-SAT Solver — Detailed Spec

**[TODO: AGENT DECISION]** Design the CP-SAT model. Here is the skeleton. You MUST fill in all constraints.

```python
from ortools.sat.python import cp_model

def solve_planning_problem(
    requests: list[PlanningRequest],
    satellites: list[Satellite],
    imaging_windows: dict[str, list[ImagingWindow]],  # key = satellite_id
    planning_horizon_hours: int = 24
) -> list[PlannedTask]:
    """
    CP-SAT model for satellite task scheduling.

    Decision variables (per satellite s, per imaging window w):
    - assign[s][w] = boolean: should satellite s use window w for a task?
    - task_assignment[request_id][satellite_id][window_index] = boolean

    Hard constraints:
    1. Each request assigned to AT MOST 1 satellite-window pair
    2. Each imaging window used for AT MOST 1 task
    3. No two tasks on same satellite overlap in time
    4. Battery conservation: cumulative power draw over horizon <= battery_capacity
    5. Storage conservation: cumulative data generated <= onboard storage
    6. Turn rate: angular distance between consecutive targets / time <= max_turn_rate

    Objective:
    Maximize weighted sum of satisfied request priorities.
    """
    model = cp_model.CpModel()

    # STEP 1: Create decision variables
    # [TODO: AGENT] Create binary decision variables assign[sat_idx][window_idx]

    # STEP 2: Constraint - Each request satisfied at most once
    # [TODO: AGENT] For each request, sum of assign variables across all sat/window combos <= 1

    # STEP 3: Constraint - Window capacity (each window used at most once)
    # [TODO: AGENT] For each window, sum of assign variables across all requests <= 1

    # STEP 4: Constraint - No time overlap on same satellite
    # [TODO: AGENT] For each pair of tasks on same satellite, enforce non-overlap
    # Use CumulativeInterval or manual time inequality

    # STEP 5: Constraint - Battery limit
    # [TODO: AGENT] Sum(power_draw[w] * assign[s][w] for all w) <= battery_capacity for each s

    # STEP 6: Constraint - Storage limit
    # [TODO: AGENT] Similar to battery: data_volume(w) * assign[s][w] <= storage_capacity

    # STEP 7: Objective - Maximize priority-weighted satisfied requests
    # [TODO: AGENT] objective = sum(priority[r] * request_satisfied[r] for all r)
    # model.Maximize(objective)

    # STEP 8: Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # STEP 9: Extract solution
    # [TODO: AGENT] Convert binary assignments to PlannedTask objects
    # Return empty list if status == CpSolver.INFEASIBLE

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return extract_tasks(solver, assign_vars, imaging_windows, satellites)
    else:
        return []  # Or raise InfeasibleException depending on caller preference
```

### 4.5 Physics Validator — Detailed Spec

After solver output, EACH task MUST pass these physics checks:

```python
def validate_task(task: PlannedTask, satellite: Satellite) -> ValidationResult:
    """
    Validate that a planned task is physically possible.

    Checks:
    1. Elevation angle at AoS >= satellite.min_elevation_deg
    2. Solar illumination at target >= 10% (not in Earth shadow)
    3. Task duration <= ground station visibility window
    4. Power consumption over task duration <= battery remaining
    5. Data size estimated <= remaining storage
    6. Turn rate between consecutive tasks on same satellite is feasible
    7. Downlink window exists after imaging (if data must be transmitted same orbit)
    """
```

**Validation result schema:**
```json
{
  "passed": true,
  "violations": [],
  "warnings": ["Battery margin tight (<10%)"],
  "details": {
    "elevation_at_aos_deg": 42.5,
    "solar_illumination_pct": 85.0,
    "battery_remaining_pct": 34.0,
    "storage_remaining_gb": 12.4,
    "turn_rate_observed_deg_s": 1.2,
    "turn_rate_limit_deg_s": 2.0
  }
}
```

### 4.6 Frontend — Screen Specifications

**Screen 1: Planning Dashboard**
```
Layout:
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo | Planning  |  Evaluations  |  Settings  | [Avatar]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ New Planning Request ────────────────────────────────┐  │
│  │                                                       │  │
│  │  [Text area: "Describe your planning request..."]     │  │
│  │                                                       │  │
│  │  [Generate Schedule Button]                           │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Recent Requests ─────────────────────────────────────┐  │
│  │  Request              │ Status    │ Created    │ Action│  │
│  │  Image Tokyo Bay      │ Ready     │ 2h ago     │ View  │  │
│  │  Flood zones SE Asia  │ Pending   │ 30m ago  │ View  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Screen 2: Schedule Viewer**
```
Layout:
┌─────────────────────────────────────────────────────────────┐
│  Back ←  Schedule: "Image Tokyo Bay"       [Export PDF]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Intent Summary ──────────────────────────────────────┐  │
│  │  Region: Tokyo Bay  |  Resolution: <3m  |  Priority: Normal│
│  │  [Edit Intent]                                          │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Map View ─────────────────────────────────────────────┐  │
│  │  [Leaflet/Mapbox map showing:                           │  │
│  │    - Target area (red polygon)                          │  │
│  │    - Satellite ground tracks (blue lines)               │  │
│  │    - Planned imaging windows (green markers)            │  │
│  │    - Ground stations (tower icons)                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Gantt Chart ──────────────────────────────────────────┐  │
│  │  Time →                                    [Zoom Controls]│
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ Sattelite A: [===== Task 1 =====][=== Task 2 ===]│  │  │
│  │  │ Sattelite B: [==== Task 3 ======]                │  │  │
│  │  │ Sattelite C:           [=== Task 4 ===]          │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Task Details (selected) ──────────────────────────────┐  │
│  │  Satellite: NORSAT-1                                    │  │
│  │  Acquisition: 2026-06-14 08:23:15 UTC                  │  │
│  │  Duration: 30 seconds                                   │  │
│  │  Estimated data: 240 MB                                 │  │
│  │  Battery delta: -2.1%                                   │  │
│  │  Validation: PASSED ✓                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.7 Seed Data for MVP

The system ships with these pre-loaded satellites (real TLE data):

| Name | NORAD ID | Type | Resolution | Swath | Notes |
|------|----------|------|-----------|-------|-------|
| WorldView-3 | 40697 | eo_multispectral | 0.31m | 13.1km | Commercial HD |
| RapidEye | 37840 | eo_multispectral | 6.5m | 60km | European EO |
| Sentinel-2A | 40697 | eo_multispectral | 10m | 290km | ESA free data |
| Landsat-9 | 49260 | eo_multispectral | 15m | 185km | USGS/NASA |

[TODO: AGENT] Fetch real current TLE data from CelesTrak API for these satellites at application startup and store in the database. Update TLE every 24 hours.

CelesTrak API endpoint: `https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle`

---

## 5. PRODUCT 2: RIGOR — ORBITAL AI ROBUSTNESS EVALUATION

### 5.1 User Stories

**US-B1: Submit Model for Evaluation**
- AS AN AI algorithm engineer at a remote sensing company
- I WANT to upload my PyTorch model and select degradation types to test
- SO THAT I can get a robustness report before deploying to orbit
- GIVEN I am logged in
- WHEN I upload model (.pt/.onnx/.pb) and select test parameters
- THEN the system creates an evaluation job and returns a job ID

**US-B2: View Evaluation Results**
- AS AN AI algorithm engineer
- I WANT to see detailed robustness metrics per degradation type
- SO THAT I can understand which scenarios my model fails
- GIVEN an evaluation job is complete
- WHEN I open the results page
- THEN I see:
  - Overall robustness score (0-100)
  - Per-degradation breakdown with charts
  - Comparison against industry baseline
  - Human-readable recommendations
  - Exportable PDF report

**US-B3: Continuous Monitoring**
- AS A satellite operator
- I WANT to track my deployed model's in-orbit performance over time
- SO THAT I can detect degradation caused by radiation
- GIVEN a model is deployed on a satellite
- WHEN I compare in-orbit metrics against baseline lab metrics
- THEN the system alerts me when performance drops more than X%

### 5.2 Degradation Injection Engine — Detailed Spec

Five degradation types, each with configurable severity levels:

**D1: Cloud Cover**
```python
def inject_cloud_degradation(
    image: np.ndarray,
    severity: float  # 0.0 (none) to 1.0 (severe)
) -> np.ndarray:
    """
    Simulates cloud cover over satellite imagery.

    At severity=0.0: no clouds
    At severity=0.3: scattered thin clouds (~30% coverage)
    At severity=0.6: moderate stratiform clouds (~60% coverage)
    At severity=0.9: thick cumulus clouds (~90% coverage)

    Uses realistic cloud texture synthesis based on:
    - Weibull-distributed cloud opacity
    - Multi-scale Perlin noise for cloud structure
    - Spectral properties matching actual satellite cloud data
    """
```

**D2: Illumination Changes**
```python
def inject_illumination_degradation(
    image: np.ndarray,
    sun_angle_deg: float,   # solar zenith angle (0=sun directly overhead, 90=horizon)
    shadow_ratio: float,    # fraction of image in shadow
    time_of_day: str        # "dawn" | "day" | "dusk" | "night"
) -> np.ndarray:
    """
    Simulates different lighting conditions.
    At dawn/dusk: long shadows, low contrast, color shift toward orange/red
    At night: extremely low light, noise-dominated (simulate with sensor noise)
    """
```

**D3: Sensor Noise**
```python
def inject_sensor_noise(
    image: np.ndarray,
    snr_db: float,          # signal-to-noise ratio in dB
    read_noise_e: float,    # electrons
    dark_current_rate: float # electrons/second/pixel
) -> np.ndarray:
    """
    Simulates CMOS/CCD sensor noise from radiation exposure.
    Adds:
    - Gaussian read noise
    - Poisson photon shot noise
    - Fixed-pattern noise (from radiation-induced pixel defects)
    - Cosmic ray strikes (sparse bright pixels)
    """
```

**D4: Attitude Jitter**
```python
def inject_attitude_jitter(
    image: np.ndarray,
    pitch_arcsec: float,    # pitch jitter in arcseconds
    roll_arcsec: float,     # roll jitter
    yaw_arcsec: float,      # yaw jitter
    exposure_time_ms: float # exposure duration
) -> np.ndarray:
    """
    Simulates motion blur from satellite attitude instability.
    Uses directional blur kernel based on jitter vector.
    """
```

**D5: Radiation Effects (Weight Perturbation)**
```python
def inject_radiation_weight_shift(
    model: torch.nn.Module,
    flip_probability: float,  # 0.0 to 0.01 (fraction of weights flipped)
    drift_magnitude: float    # 0.0 to 0.1 (weight perturbation scale)
) -> torch.nn.Module:
    """
    Simulates radiation-induced bit flips and weight drift in neural network.

    Two mechanisms:
    1. Single-event upset (SEU): Random weight bits flip (binary)
    2. Total ionizing dose (TID): Gradual weight drift (continuous)

    Returns modified model copy (does not mutate original).
    """
```

### 5.3 Evaluation Pipeline — Step by Step

```
Step 1: Model Loading
  Input: model file (.pt/.onnx/.pb)
  Action: Load model, detect architecture, determine input shape
  Output: model handle + input_spec

Step 2: Baseline Dataset Loading
  Input: baseline_dataset_id OR upload user dataset
  Action: Load images, run model through them
  Output: baseline_metrics {accuracy, f1, mAP}

Step 3: Degradation Injection (per type)
  Input: model, baseline dataset, degradation_type, severity_levels
  Action: For each severity level (none/light/moderate/severe/critical):
    a. Apply degradation to dataset images
    b. Run degraded images through model
    c. Compute metrics on degraded outputs
  Output: metrics_per_severity dict

Step 4: Robustness Scoring
  Input: metrics_per_severity for all degradation types
  Action: Compute composite score:
    score = Σ(weight_i * accuracy_drop_i) for each degradation type
    weight_i based on mission profile (user selects: tropical, polar, urban...)
  Output: robustness_score (0-100), breakdown by type

Step 5: Report Generation
  Input: All results
  Action: Generate structured result + human-readable recommendations
  Output: EvaluationResult records in DB + JSON report
```

### 5.4 Frontend — Evaluation Dashboard

```
Layout:
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo | Planning  |  Evaluations  |  Settings  | [Avatar]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ New Evaluation ───────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Model Name: [________________________]                 │  │
│  │  Model File: [Choose File (.pt/.onnx/.pb)]              │  │
│  │  Model Type: [Classification ▼]                         │  │
│  │  Sensor Type: [Optical ▼]                               │  │
│  │                                                         │  │
│  │  Degradation Types to Test:                             │  │
│  │  [✓] Cloud Cover   [✓] Illumination   [✓] Sensor Noise  │  │
│  │  [✓] Attitude Jitter  [✓] Radiation Effects             │  │
│  │                                                         │  │
│  │  Mission Profile (for weighting):                       │  │
│  │  [Tropical ▼]                                           │  │
│  │                                                         │  │
│  │  [Start Evaluation Button]                              │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Job Queue ────────────────────────────────────────────┐  │
│  │  Job              │ Model Type │ Status    │ Progress  │  │
│  │  ShipDetector_v2│ Detection  │ Running   │ 67%       │  │
│  │  CloudFilter_v1 │ Classif.   │ Completed │ 100%      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Results Display:**
```
┌─ Robustness Score Card ──────────────────────────────────┐
│  Overall Score: 72/100                                    │
│  Grade: B (Acceptable for most environments)              │
│                                                           │
│  ┌─ Degradation Breakdown ─────────────────────────────┐  │
│  │                                                     │  │
│  │  Cloud Cover:    ████████████░░  78/100  [ACCEPT]   │  │
│  │  Illumination:   ████████████░░  75/100  [ACCEPT]   │  │
│  │  Sensor Noise:   ██████████░░░░  65/100  [CAUTION]  │  │
│  │  Attitude Jitter:███████████░░░  70/100  [ACCEPT]   │  │
│  │  Radiation:      ██████████░░░░  62/100  [CAUTION]  │  │
│  │                                                     │  │
│  │  ★ Cloud cover causes largest accuracy drop: -22%   │  │
│  │  ★ Consider cloud-penetration preprocessing         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─ Detail Chart ──────────────────────────────────────┐  │
│  │  [Line chart: Accuracy vs Severity for each type]   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 Baseline Datasets for MVP

Ship with these free datasets for testing:

| Dataset | Images | Type | License | Link |
|---------|--------|------|---------|------|
| EuroSAT | 27k | Classification | Creative Commons | https://github.com/phelber/eurosat |
| DOTA | 28k | Object Detection | Academic | https://captain-whu.github.io/DOTA/ |
| SEN12MS | 44k | Multi-temporal | Academic | https://github.com/martinis-io/SEN12MS |

---

## 6. API SPECIFICATION

### 6.1 Authentication

```
POST /api/v1/auth/register
Body: { "email": string, "password": string, "name": string }
Response 201: { "user_id": uuid, "email": string, "plan": "free" }

POST /api/v1/auth/login
Body: { "email": string, "password": string }
Response 200: { "access_token": string, "refresh_token": string, "user": User }

POST /api/v1/auth/refresh
Body: { "refresh_token": string }
Response 200: { "access_token": string }

GET /api/v1/auth/me
Headers: Authorization: Bearer <token>
Response 200: User
```

### 6.2 Planning API

```
GET /api/v1/satellites
Headers: Authorization: Bearer <token>
Response 200: [Satellite]

POST /api/v1/planning/requests
Headers: Authorization: Bearer <token>
Body: { "raw_input": string }
Response 200: {
  "request_id": uuid,
  "status": "planning",
  "parsed_intent": { /* from LLM */ },
  "confidence": { /* from LLM */ }
}

GET /api/v1/planning/requests/{request_id}
Headers: Authorization: Bearer <token>
Response 200: {
  "request": PlanningRequest,
  "tasks": [PlannedTask],
  "validation": ValidationResult
}

POST /api/v1/planning/requests/{request_id}/cancel
Headers: Authorization: Bearer <token>
Response 200: { "status": "cancelled" }

POST /api/v1/planning/requests/{request_id}/replan
Headers: Authorization: Bearer <token>
Body: { "priority_override": "high|urgent", "satellite_swap": uuid }
Response 200: { "tasks": [PlannedTask], "changes": string }
```

### 6.3 Evaluation API

```
POST /api/v1/evaluations
Headers: Authorization: Bearer <token>
Body: {
  "model_name": string,
  "model_type": "classification|detection|segmentation",
  "sensor_type": "optical|multispectral|hyperspectral",
  "degradation_types": ["cloud", "illumination", "noise", "jitter", "radiation"],
  "mission_profile": "tropical|polar|urban|arctic"
}
Response 201: {
  "job_id": uuid,
  "status": "pending",
  "estimated_completion_minutes": int
}

GET /api/v1/evaluations/{job_id}
Headers: Authorization: Bearer <token>
Response 200: {
  "job": EvaluationJob,
  "results": [EvaluationResult],
  "status": "pending|running|completed|failed",
  "progress_percent": int
}

GET /api/v1/evaluations/{job_id}/report
Headers: Authorization: Bearer <token>
Response 200: {
  "summary": string,
  "scores": { "overall": float, "per_degradation_type": dict },
  "metrics": [EvaluationResult.metrics],
  "recommendations": [string]
}
```

### 6.4 Error Response Format

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human-readable error message",
    "details": { /* optional, additional context */ },
    "retryable": true | false
  }
}
```

**Error codes:**
- `PARSING_FAILED` — LLM intent parsing failed (retryable)
- `INFEASIBLE` — No feasible schedule found (not retryable, try relaxing constraints)
- `VALIDATION_FAILED` — Scheduled task failed physics check (retryable, solver will try alternatives)
- `MODEL_LOAD_FAILED` — Cannot load uploaded model (not retryable, check file format)
- `INSUFFICIENT_STORAGE` — Not enough storage for evaluation (retryable, free some space)
- `RATE_LIMIT_EXCEEDED` — Too many requests (retryable with backoff)

---

## 7. FRONTEND SPECIFICATION

### 7.1 Technology Choices

```
Framework:      React 18 + TypeScript + Vite
UI Components:  shadcn/ui (Radix primitives + Tailwind)
State:          React Query (server state) + Zustand (client state)
Maps:           Leaflet + react-leaflet
Charts:         Recharts
Tables:         TanStack Table
Forms:          React Hook Form + Zod validation
HTTP Client:    Axios with interceptors
Styling:        TailwindCSS 3
Icons:          Lucide React
```

### 7.2 Component Hierarchy

```
App (BrowserRouter)
├── Layout (Sidebar + Main Content)
│   ├── Header
│   │   ├── Logo
│   │   ├── NavigationTabs (Planning / Evaluations / Settings)
│   │   └── UserMenu (avatar + dropdown)
│   ├── MainContent
│   │   ├── PlanningDashboard (route: /planning)
│   │   │   ├── NewRequestForm
│   │   │   ├── RequestHistoryTable
│   │   │   └── ScheduleViewerModal (when viewing a schedule)
│   │   │       ├── IntentSummary
│   │   │       ├── MapView (Leaflet)
│   │   │       ├── GanttChart
│   │   │       └── TaskDetailPanel
│   │   ├── EvaluationDashboard (route: /evaluations)
│   │   │   ├── NewEvaluationForm
│   │   │   ├── JobQueueTable
│   │   │   └── ResultDisplay
│   │   │       ├── ScoreCard
│   │   │       ├── DegradationBreakdownChart
│   │   │       ├── AccuracyVsSeverityChart
│   │   │       └── RecommendationPanel
│   │   └── SettingsPage (route: /settings)
│   │       ├── AccountSettings
│   │       ├── APIKeys
│   │       └── Subscription
```

### 7.3 Form Validation Schemas (Zod)

```typescript
// planning/validation.ts
import { z } from "zod";

export const NewPlanningRequestSchema = z.object({
  raw_input: z.string()
    .min(10, "Please provide at least 10 characters")
    .max(500, "Maximum 500 characters"),
});

export const NewEvaluationSchema = z.object({
  model_name: z.string().min(1, "Model name is required").max(200),
  model_type: z.enum(["classification", "detection", "segmentation"]),
  sensor_type: z.enum(["optical", "multispectral", "hyperspectral"]),
  degradation_types: z.array(z.enum(["cloud", "illumination", "noise", "jitter", "radiation"]))
    .min(1, "Select at least one degradation type"),
  mission_profile: z.enum(["tropical", "polar", "urban", "arctic"]).optional(),
  model_file: z.instanceof(File).optional(), // validated server-side for format
});
```

---

## 8. IMPLEMENTATION ORDER FOR AI AGENT

**Follow this EXACT order. Do NOT skip ahead.**

### Phase 1: Infrastructure (Day 1-3)
1. Initialize project with Vite + React + TypeScript + Python FastAPI template
2. Set up Docker Compose (PostgreSQL + Redis + Backend + Frontend)
3. Configure Alembic for database migrations
4. Set up CI (pytest for backend, vitest for frontend)
5. [TODO: AGENT] Choose your package manager and initialize. Document choice.

### Phase 2: Data Layer (Day 3-5)
6. Implement all SQLAlchemy models from Section 3
7. Write Alembic migration to create all tables
8. Write seed data script (satellites, ground stations)
9. Write unit tests for models

### Phase 3: Authentication (Day 5-7)
10. Implement JWT auth (register, login, refresh, me endpoints)
11. Implement password hashing (bcrypt)
12. Write integration tests for auth
13. Create frontend AuthContext + login/register pages

### Phase 4: Orbit Engine (Day 7-12)
14. Implement `calculate_overpass_windows()` using skyfield + sgp4
15. Implement `calculate_imaging_windows()` with sun angle filtering
16. Write test with ISS TLE data over Tokyo (verify: ~3-4 windows per day)
17. Create API endpoint `GET /api/v1/orbit/windows`
18. Create API endpoint `GET /api/v1/satellites`

### Phase 5: LLM Intent Parser (Day 12-15)
19. Implement LLM parser with LangChain + gpt-4o
20. Implement strict JSON output parsing with Pydantic validation
21. Handle parsing failures with retry logic (max 3 retries)
22. Create API endpoint `POST /api/v1/planning/parse`
23. Write test with 10 sample queries, verify 80%+ parse accuracy

### Phase 6: CP-SAT Solver (Day 15-21)
24. **This is the hardest part.** Follow the skeleton in Section 4.4 carefully.
25. Implement all 7 constraint types
26. Implement objective function (weighted priority maximization)
27. Implement solution extraction to PlannedTask objects
28. Write test with 5 satellites, 3 requests — verify optimal solution

### Phase 7: Physics Validator (Day 21-24)
29. Implement all 7 validation checks from Section 4.5
30. Create API endpoint `POST /api/v1/planning/validate`
31. Write test: feed an infeasible task (e.g., elevation < min_elevation)

### Phase 8: Planning End-to-End (Day 24-28)
32. Wire together: LLM Parse → Overpass Windows → CP-SAT → Validator
33. Implement `POST /api/v1/planning/requests` endpoint
34. Implement async task processing (Celery or background tasks)
35. Implement `GET /api/v1/planning/requests/{id}` with status polling

### Phase 9: Frontend — Planning (Day 28-35)
36. Create Planning Dashboard (Section 4.6 Screen 1)
37. Create Schedule Viewer with Map + Gantt (Section 4.6 Screen 2)
38. Implement request creation flow (Section 4.1 US-1)
39. Implement schedule viewing flow (Section 4.1 US-2)
40. Implement emergency replan (Section 4.1 US-4)

### Phase 10: Rigor — Core (Day 35-42)
41. Implement 5 degradation injection functions (Section 5.2)
42. Implement model loader (handle .pt, .onnx, .pb)
43. Implement evaluation pipeline (Section 5.3, all 5 steps)
44. Implement robustness scoring algorithm
45. Create API endpoints (Section 6.3)

### Phase 11: Frontend — Evaluation (Day 42-49)
46. Create Evaluation Dashboard (Section 5.4)
47. Create Results Display with charts (Section 5.4)
48. Implement upload flow
49. Implement job status polling with progress bar

### Phase 12: Polish & Testing (Day 49-56)
50. End-to-end integration tests
51. Responsive design testing
52. Performance testing (solver should complete < 10s for MVP scope)
53. Documentation updates
54. Bug fixes

### Phase 13: Deploy
55. Docker production build
56. Deploy to Railway/Vercel
57. Smoke test on live environment

---

## APPENDIX A: Known Technical Constraints

1. **TLE data becomes stale.** Re-fetch from CelesTrak every 24 hours. The SGP4 accuracy degrades after ~7 days.

2. **LLM cost.** Each intent parsing call costs ~$0.01. Budget: ~$300/month for 30K requests.

3. **CP-SAT solves slowly for large instances.** For MVP (single satellite, up to 50 imaging windows), solve time should be < 5 seconds. For multi-satellite (Phase 2), expect 30-60 seconds.

4. **Model upload size limit.** MVP: 500MB max. Use streaming upload to avoid memory issues.

5. **Evaluation time.** A full evaluation (5 degradation types × 5 severity levels × 1000 images) takes ~10-30 minutes. Use async job processing with WebSocket or polling for progress updates.

6. **Radiation modeling is approximate.** The MVP uses weight perturbation as proxy for radiation effects. Real radiation testing requires physical irradiation or specialized tools like MCNP. Document this limitation.

## APPENDIX B: External API References

| Service | API | Purpose |
|---------|-----|---------|
| CelesTrak | `celestrak.org` | TLE data for all cataloged satellites |
| OpenAI | `api.openai.com` | gpt-4o for intent parsing |
| Google OR-Tools | PyPI: `ortools` | CP-SAT solver |
| Skyfield | PyPI: `skyfield` | Orbital propagation |
| SGP4 | PyPI: `sgp4` | Orbit propagation engine |
| Leaflet | npm: `leaflet` | Map rendering |

## APPENDIX C: Glossary

| Term | Definition |
|------|-----------|
| TLE | Two-Line Element set — standard format for satellite orbital data |
| SGP4 | Simplified General Perturbations 4 — orbit propagation model |
| AoS | Acquisition of Signal — when ground station first sees satellite |
| LOS | Loss of Signal — when ground station loses satellite |
| SSO | Sun-Synchronous Orbit — orbit where pass time is constant |
| EO | Earth Observation — satellite imaging of Earth |
| CP-SAT | Constraint Programming - SATurability — OR-Tools constraint solver |
| SEU | Single Event Upset — radiation-induced bit flip in electronics |
| TID | Total Ionizing Dose — cumulative radiation damage to electronics |
| SWaP-C | Size, Weight, Power, and Cost — key satellite design constraints |
