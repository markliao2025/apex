import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import DemoReplayPage from "./DemoReplayPage";

const api = vi.hoisted(() => ({
  listConstellations: vi.fn(),
  listSatellites: vi.fn(),
  createReplay: vi.fn(),
  planningImpact: vi.fn(),
  exportReplay: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  tenancyApi: {
    listConstellations: api.listConstellations,
    listSatellites: api.listSatellites,
  },
  demoApi: {
    createReplay: api.createReplay,
    planningImpact: api.planningImpact,
    exportReplay: api.exportReplay,
  },
}));

const constellation = {
  id: "constellation-1",
  organization_id: "org-1",
  slug: "demo",
  name: "Demo constellation",
  description: null,
  is_demo: true,
  role: "owner",
  satellite_count: 1,
  created_at: "2024-05-31T12:00:00Z",
  updated_at: "2024-05-31T12:00:00Z",
};

const replay = {
  schema_version: "apex.demo.replay.v1",
  replay_id: "replay-1",
  fixture_id: "apex-synthetic-001",
  fixture_sha256: "a".repeat(64),
  event_id: "APEX-SYNTHETIC-001",
  created_at_utc: "2024-05-31T12:00:00Z",
  tca_utc: "2024-06-01T12:00:00Z",
  objects: {
    primary: { catalog_id: "100001", name: "PRIMARY" },
    secondary: { catalog_id: "100002", name: "SECONDARY" },
  },
  relative_state: { miss_distance_m: 245, relative_speed_m_s: 14250 },
  risk: {
    collision_probability: 0.00012,
    source: "provided",
    method: "synthetic_demo_value",
  },
  labels: {
    pc_origin: "provided",
    apex_computed_pc: false,
    physics_verified: false,
  },
  data_quality: {
    grade: "degraded",
    covariance_available: false,
    pc_reproducible: false,
    explanation: "Covariance is unavailable.",
  },
  warnings: [],
  limitations: ["Synthetic event"],
};

describe("DemoReplayPage", () => {
  it("renders truthful replay and before/after impact", async () => {
    api.listConstellations.mockResolvedValue([constellation]);
    api.listSatellites.mockResolvedValue([
      {
        constellation_id: constellation.id,
        display_name: null,
        enabled: true,
        satellite: {
          id: "satellite-1",
          norad_id: "40697",
          name: "Sentinel-2A",
          tle_epoch: "2024-05-31T12:00:00Z",
          orbit_type: "sso",
          payload_type: "eo_multispectral",
          max_resolution_m: 10,
          swath_width_km: 290,
        },
      },
    ]);
    api.createReplay.mockResolvedValue(replay);
    api.planningImpact.mockResolvedValue({
      schema_version: "apex.demo.planning-impact.v1",
      algorithm_version: "apex.planning-impact.v1",
      evidence_sha256: "b".repeat(64),
      evaluation_time_utc: "2024-05-31T12:00:00Z",
      before: { task_count: 1, task_ids: ["task"], objective_value: 1000, solver_status: "optimal", solve_time_ms: 1 },
      after: { task_count: 0, task_ids: [], objective_value: 0, solver_status: "optimal", solve_time_ms: 1 },
      diff: {
        retained_task_ids: [],
        removed_task_ids: ["task"],
        reassigned_task_ids: [],
        objective_delta: -1000,
        affected_window: {
          start_utc: "2024-06-01T11:58:00Z",
          end_utc: "2024-06-01T12:02:00Z",
        },
      },
      physics_verified: false,
      limitations: ["This is hypothetical."],
    });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <DemoReplayPage />
      </QueryClientProvider>,
    );

    expect(await screen.findByLabelText("Constellation")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Hypothetically unavailable satellite"),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /run deterministic replay/i }),
    );
    expect(await screen.findByText(/provided risk, degraded/i)).toBeInTheDocument();
    expect(screen.getByText(/pc provided · not computed/i)).toBeInTheDocument();
    expect(screen.getByText(/not flight-certified/i)).toBeInTheDocument();
    expect(screen.getByText(/no maneuver is executed by apex/i)).toBeInTheDocument();

    const compare = await screen.findByRole("button", {
      name: /compare schedule/i,
    });
    await screen.findByRole("option", { name: "Sentinel-2A" });
    fireEvent.click(compare);
    expect(
      await screen.findByText(/schedule comparison complete/i),
    ).toBeInTheDocument();
    expect(screen.getByText("1 planned task")).toBeInTheDocument();
    expect(screen.getByText("0 planned task")).toBeInTheDocument();
    expect(screen.getByText(/impact sha256:/i)).toHaveTextContent("b".repeat(64));
  });
});
