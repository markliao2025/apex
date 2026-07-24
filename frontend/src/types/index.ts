// ── API Types ────────────────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
    retryable?: boolean;
  };
}

// ── Auth Types ────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  user: User;
}

export type OrganizationRole = "owner" | "operator" | "viewer";

export interface Organization {
  id: string;
  slug: string;
  name: string;
  role: OrganizationRole;
}

export interface Constellation {
  id: string;
  organization_id: string;
  slug: string;
  name: string;
  description: string | null;
  is_demo: boolean;
  role: OrganizationRole;
  satellite_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConstellationSatellite {
  constellation_id: string;
  display_name: string | null;
  enabled: boolean;
  satellite: Satellite;
}

export interface DemoReplay {
  schema_version: string;
  replay_id: string;
  fixture_id: string;
  fixture_sha256: string;
  event_id: string;
  created_at_utc: string;
  tca_utc: string;
  objects: {
    primary: { catalog_id: string; name: string };
    secondary: { catalog_id: string; name: string };
  };
  relative_state: {
    miss_distance_m: number;
    relative_speed_m_s: number;
  };
  risk: {
    collision_probability: number;
    source: "provided";
    method: string;
  };
  labels: {
    pc_origin: "provided";
    apex_computed_pc: false;
    physics_verified: false;
  };
  data_quality: {
    grade: "degraded";
    covariance_available: false;
    pc_reproducible: false;
    explanation: string;
  };
  warnings: string[];
  limitations: string[];
}

export interface PlanningImpact {
  schema_version: string;
  algorithm_version: string;
  evidence_sha256: string;
  evaluation_time_utc: string;
  before: {
    task_count: number;
    task_ids: string[];
    objective_value: number;
    solver_status: string;
    solve_time_ms: number;
  };
  after: {
    task_count: number;
    task_ids: string[];
    objective_value: number;
    solver_status: string;
    solve_time_ms: number;
  };
  diff: {
    retained_task_ids: string[];
    removed_task_ids: string[];
    reassigned_task_ids: string[];
    objective_delta: number;
    affected_window: { start_utc: string; end_utc: string };
  };
  physics_verified: false;
  limitations: string[];
}

// ── Planning Types ────────────────────────────────────────────────────────────

export interface BoundingBox {
  sw_lat: number;
  sw_lng: number;
  ne_lat: number;
  ne_lng: number;
}

export interface ConfidenceScores {
  region_description: number;
  resolution_requirement_m: number;
  time_window_days: number;
  priority: number;
}

export interface ParsedIntent {
  region_description?: string | null;
  bounding_box?: BoundingBox | null;
  event_filter?: string | null;
  resolution_requirement_m?: number | null;
  time_window_days?: number | null;
  priority: "low" | "normal" | "high" | "urgent";
  sensor_preference?: string | null;
  confidence?: ConfidenceScores | null;
  uncertainty_notes?: string[];
}

export interface PlannedTask {
  id: string;
  satellite_name: string | null;
  satellite_id: string;
  target_area: Record<string, unknown>;
  event_window: {
    aos_time: string;
    los_time: string;
    max_elevation_deg: number;
  };
  resource_allocation: {
    power_w: number;
    storage_mb: number;
    battery_delta_percent: number;
  };
  solver_status: string;
  validator_status: string;
  priority_score: number;
  created_at: string;
}

export interface PlanningRequest {
  id: string;
  constellation_id: string;
  raw_input: string;
  parsed_intent: Record<string, unknown> | null;
  status: string;
  error_code?: string | null;
  error_message?: string | null;
  tasks: PlannedTask[];
  created_at: string;
  updated_at: string;
}

export interface PlanningParseResponse {
  status: string;
  parsed_intent: ParsedIntent;
  confidence?: ConfidenceScores | null;
}

// ── Satellite Types ───────────────────────────────────────────────────────────

export interface Satellite {
  id: string;
  norad_id: string;
  name: string;
  tle_epoch: string;
  orbit_type: string;
  payload_type: string;
  max_resolution_m: number;
  swath_width_km: number;
}

export interface OverpassWindow {
  aos: string;
  los: string;
  max_elevation: number;
  duration_seconds: number;
}

export interface GroundStation {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  altitude_m: number;
  band: string;
  antenna_diameter_m: number;
}

// ── Orbit Types ───────────────────────────────────────────────────────────────

export interface ImagingWindow {
  aos: string;
  los: string;
  max_elevation_deg: number;
  illumination_pct: number;
  duration_seconds: number;
}

export interface GroundTrackPoint {
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude_km: number;
}
