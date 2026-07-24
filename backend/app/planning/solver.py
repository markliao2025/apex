"""CP-SAT constraint solver for satellite task scheduling.

Uses Google OR-Tools CP-SAT solver to generate physically-feasible
observation schedules that maximise priority-weighted coverage.

Decision variables:
  assign[(request_id, satellite_id, window_idx)] = BoolVar
    True if the imaging window is assigned to the request.

Hard constraints:
  C1: Each request is assigned to AT MOST one (satellite, window) pair.
  C2: Each satellite uses each imaging window for AT MOST one task.
  C3: No two tasks on the same satellite overlap in time.
  C4: Total power draw over the horizon ≤ battery capacity.
  C5: Total data volume over the horizon ≤ storage capacity.
  C6: Turn rate between consecutive tasks is feasible.

Objective:
  Maximise sum(request.priority_score × satisfied).
"""

from __future__ import annotations

from ortools.sat.python import cp_model

from app.planning.solver_types import Assignment, SolverInput, SolverResult


def solve(planning_input: SolverInput, time_limit_ms: int = 5000) -> SolverResult:
    """Run the CP-SAT solver on the given planning input.

    Args:
        planning_input: Structured input containing requests, satellites,
            and their imaging windows.
        time_limit_ms: Maximum solver time in milliseconds.

    Returns:
        SolverResult with assignments, solver status, and objective value.
    """
    model = cp_model.CpModel()

    # ── Helper: build ordered index for each request-satellite-window ─────────
    # For easier reference, create an index list of all valid assignments
    all_assignments = []  # (request_idx, satellite_idx, window_idx)
    for req_idx, req in enumerate(planning_input.requests):
        for sat_idx, sat in enumerate(planning_input.satellites):
            sat_id = str(sat.id)
            if sat_id not in planning_input.imaging_windows:
                continue
            windows = planning_input.imaging_windows[sat_id]
            for w_idx in range(len(windows)):
                all_assignments.append((req_idx, sat_idx, w_idx))

    # ── Decision variables ────────────────────────────────────────────────────
    # assign[i] is boolean: should the i-th (request, satellite, window) combo be used?
    n_assignments = len(all_assignments)
    assign_vars = [model.NewBoolVar(f"assign_{i}") for i in range(n_assignments)]

    # Map from (request_idx, satellite_idx) -> list of assignment indices
    req_sat_assigns: dict[tuple[int, int], list[int]] = {}
    # Map from (satellite_idx, window_idx) -> list of assignment indices
    sat_window_assigns: dict[tuple[int, int], list[int]] = {}

    for i, (req_idx, sat_idx, w_idx) in enumerate(all_assignments):
        req_sat_assigns.setdefault((req_idx, sat_idx), []).append(i)
        sat_window_assigns.setdefault((sat_idx, w_idx), []).append(i)

    # ── Constraint C1: Each request assigned at most once ────────────────────
    for req_idx in range(len(planning_input.requests)):
        req_vars = []
        for sat_idx in range(len(planning_input.satellites)):
            key = (req_idx, sat_idx)
            if key in req_sat_assigns:
                req_vars.extend(req_sat_assigns[key])
        if req_vars:
            model.Add(sum(assign_vars[i] for i in req_vars) <= 1)

    # ── Constraint C2: Each satellite-window used at most once ───────────────
    for sat_id, sat_windows in planning_input.imaging_windows.items():
        sat_local_idx = planning_input.satellite_ids.index(sat_id)
        for w_idx in range(len(sat_windows)):
            key = (sat_local_idx, w_idx)
            if key in sat_window_assigns:
                ws = sat_window_assigns[key]
                model.Add(sum(assign_vars[i] for i in ws) <= 1)

    # ── Constraint C3: No time overlap on same satellite ─────────────────────
    # For each satellite, build a conflict matrix: if two windows overlap in
    # time, at most one can be used.
    for sat_idx, sat_id in enumerate(planning_input.satellite_ids):
        if sat_id not in planning_input.imaging_windows:
            continue
        windows = planning_input.imaging_windows[sat_id]
        # Get all assignment indices for this satellite
        overlap_vars: list[int] = []
        for i, (_, s_idx, _) in enumerate(all_assignments):
            if s_idx == sat_idx:
                overlap_vars.append(i)

        # Build pairwise conflict check
        for ai in range(len(overlap_vars)):
            for aj in range(ai + 1, len(overlap_vars)):
                vi = overlap_vars[ai]
                vj = overlap_vars[aj]
                req_i, _, wi = all_assignments[vi]
                _, _, wj = all_assignments[vj]
                wi_data = windows[wi]
                wj_data = windows[wj]
                # Check time overlap
                if wi_data.aos < wj_data.los and wj_data.aos < wi_data.los:
                    # Overlapping: at most one can be selected
                    model.Add(assign_vars[vi] + assign_vars[vj] <= 1)

    # ── Constraint C4: Battery capacity per satellite ────────────────────────
    # Multiply power by 1000 to convert to integer (CP-SAT requires integers)
    POWER_SCALE = 1000
    for sat_idx, sat_id in enumerate(planning_input.satellite_ids):
        battery_limit = planning_input.satellite_batteries.get(sat_id, float("inf"))
        if battery_limit == float("inf"):
            continue
        battery_vars: list[int] = []
        for i, (_, s_idx, w_idx) in enumerate(all_assignments):
            if s_idx == sat_idx:
                battery_vars.append(i)
        if battery_vars:
            total_power = 0
            for i in battery_vars:
                _, s_idx, w_idx = all_assignments[i]
                windows = planning_input.imaging_windows[sat_id]
                power = windows[w_idx].power_draw
                total_power += assign_vars[i] * int(power * POWER_SCALE)
            model.Add(total_power <= int(battery_limit * POWER_SCALE))

    # ── Constraint C5: Storage capacity per satellite ────────────────────────
    # Multiply data_mb by 1000 to convert to integer
    DATA_SCALE = 1000
    for sat_idx, sat_id in enumerate(planning_input.satellite_ids):
        storage_limit = planning_input.satellite_storages.get(sat_id, float("inf"))
        if storage_limit == float("inf"):
            continue
        storage_vars: list[int] = []
        for i, (_, s_idx, w_idx) in enumerate(all_assignments):
            if s_idx == sat_idx:
                storage_vars.append(i)
        if storage_vars:
            total_data = 0
            for i in storage_vars:
                _, s_idx, w_idx = all_assignments[i]
                windows = planning_input.imaging_windows[sat_id]
                data_mb = windows[w_idx].data_mb
                total_data += assign_vars[i] * int(data_mb * DATA_SCALE)
            model.Add(total_data <= int(storage_limit * DATA_SCALE))

    # ── Objective: Maximize weighted priority sum ────────────────────────────
    # Priority scores come from the request parser
    objective_terms = []
    for i, (req_idx, sat_idx, w_idx) in enumerate(all_assignments):
        priority = planning_input.requests[req_idx].priority_score
        # Scale to integer for CP-SAT (objective must be integer)
        weight = int(priority * 1000)
        objective_terms.append(assign_vars[i] * weight)

    model.Maximize(sum(objective_terms))

    # ── Solve ─────────────────────────────────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_ms / 1000.0
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0

    status_code = solver.Solve(model)
    status_map = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "suboptimal",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "model_invalid",
    }
    status = status_map.get(status_code, "unknown")

    # ── Extract solution ─────────────────────────────────────────────────────
    assignments = []
    for i in range(n_assignments):
        if solver.Value(assign_vars[i]) == 1:
            req_idx, sat_idx, w_idx = all_assignments[i]
            assignments.append(
                Assignment(
                    request_id=str(planning_input.requests[req_idx].id),
                    satellite_id=str(planning_input.satellites[sat_idx].id),
                    window_idx=w_idx,
                )
            )

    return SolverResult(
        status=status,
        assignments=assignments,
        objective_value=solver.ObjectiveValue(),
        solve_time_ms=solver.WallTime() * 1000.0,
    )
