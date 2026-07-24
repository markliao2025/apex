# ADR-0002: Phase 0 tenancy and SSA truth boundaries

- Status: accepted
- Date: 2026-07-24

## Context

The inherited project queried all Satellite rows, mixed stateless parsing with
database drafts, swallowed background errors, and described capabilities beyond
what the implementation could support. The open-source demonstration must be
safe to inspect and repeat without implying flightworthiness.

## Decision

- Every plan is scoped by a Constellation reachable through an
  OrganizationMembership.
- A missing scope is compatible only when the user has exactly one accessible
  constellation.
- The repository event is synthetic and CC0.
- Collision probability remains a provided input; no computed-Pc label exists
  in Phase 0.
- Missing covariance degrades quality instead of manufacturing data.
- Planning impact is a hypothetical resource-availability comparison and
  always returns `physics_verified=false`.
- Default seed/bootstrap never accesses the network.
- No LLM Agent is exposed in Phase 0.

## Consequences

The system is useful for evaluating a decision workflow and planning
consequences, but it is not an operational SSA service. Production readiness,
real orbit-solution ingestion, Pc methods and human-approved Agent orchestration
remain separately gated work.
