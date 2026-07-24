# Apex agent instructions

## Source of truth

Read these files completely before changing code:

1. `SSA_OPEN_SOURCE_PRODUCT_AND_DEVELOPMENT_PLAN.md`
2. `PHASE0_AI_EXECUTION_PLAN.md`
3. `docs/development/BASELINE.md`
4. `docs/development/phase0-log.md`

`APEX_MVP_DEVELOPMENT_PLAN.md`, `PRODUCT_REQUIREMENTS_DOC.md`, and files under
`.trae/` are historical. They may explain old code, but they do not authorize new
scope and their completion claims are not current evidence.

## Phase boundary

- Phase 0 may implement synthetic event replay, input-provided Pc, evidence export,
  constellation scoping, and hypothetical planning unavailability.
- Do not implement computed Pc, real CDM persistence, maneuver generation, autonomous
  Agents, command execution, or flight-system integration.
- Never describe provided Pc as calculated by Apex.
- Every risk page and export must state that Apex is not flight-certified and does
  not execute maneuvers.

## Engineering rules

- Use timezone-aware UTC datetimes and string catalog IDs.
- Preserve provenance, units, limitations, algorithm version, and evidence hash.
- Do not access the network in tests.
- Add or update tests for every behavior change.
- Use typed domain services; LLM output is never a source of orbital truth.
- Never commit `.env`, credentials, restricted CDM, generated build output, coverage,
  virtual environments, or dependency directories.
- Do not delete user output or historical documents without explicit approval.

