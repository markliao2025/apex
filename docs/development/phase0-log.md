# Phase 0 execution log

Last updated: 2026-07-24 (Asia/Shanghai)

This is the implementation and acceptance source of truth for Phase 0. A task is
marked **local complete** only when its code and all acceptance checks available on
this workstation pass. Docker, GitHub, public-user, and elapsed-time evidence are
recorded separately and are never inferred from local unit tests.

Safety boundary for every task: Apex is research and decision-support software,
is not flight-certified, and does not execute maneuvers. Phase 0 replays only the
repository's CC0 synthetic event and treats its Pc as input-provided.

## Current status

| Task | Status | Meaning |
|---|---|---|
| P0-00 to P0-07 | Local complete | Baseline, repository boundary, OSS policy, deterministic tests, replan, seed/time, truthful errors, and tenancy are implemented and locally verified. |
| P0-08 | Implemented; Docker acceptance pending | Zero-configuration Compose path exists, but Docker is not installed on this workstation. |
| P0-09 to P0-10 | Local complete | Synthetic replay, evidence, hypothetical unavailable window, stable planning diff, and semantic hash are verified. |
| P0-11 | Implemented; browser acceptance pending | User flow and component tests pass; manual keyboard/responsive/browser checks are still required. |
| P0-12 | Partially accepted | CI, API E2E, migrations, security scan, license scan, SBOM, and attestation workflows exist. Playwright and actual GitHub/architecture runs remain pending. |
| P0-13 | Local complete; GitHub setup pending | Build-in-public forms, roadmap, metrics, and evidence ledger exist. Discussions and repository URLs need the public remote. |
| P0-14 | Release-candidate preparation only | No public remote, tag, GitHub Release, SBOM artifact, or attestation has been produced. |
| P0-15 | Not started | Requires P0-14 plus six full calendar weeks and independent-user evidence. |

## Verification snapshot

- `make verify` passed three consecutive times on 2026-07-24.
- Each run: Ruff passed; ESLint passed; Mypy passed for 57 source files;
  TypeScript passed; 96 backend tests passed in about 28 seconds; 6 frontend
  tests passed; frontend production build passed.
- Backend line coverage: 78%.
- Synthetic fixture SHA-256:
  `a45d60780bbf80e7ef56b528358136747eb4755de362daf37a9d7bff78dce188`.
- `make audit-licenses`: 63 installed direct Python/Node packages accepted.
- Workflow, Issue-form, and Compose YAML files passed local syntax parsing.
- `npm ci --dry-run --offline` accepted the lockfile and identified only the two
  intentionally removed React-Leaflet packages.
- Expected dependency warnings remain: `passlib` uses Python's deprecated
  `crypt`, `python-jose` internally uses `datetime.utcnow()`, and React Router
  reports opt-in notices for its future v7 behavior. They do not fail Phase 0.

## P0-00 — Baseline and safety

- Status: local complete.
- Commit: pending initial signed source commit at the time of this entry.
- Changed files: `docs/development/BASELINE.md`, this log.
- Commands run: runtime inventory; backend tests with timeout; Ruff; Mypy;
  ESLint; Vitest; TypeScript build; generated/binary/secret inventory.
- Result: the inherited repository state, test failures, missing Docker, absent
  Git history, generated directories, and unverified assets were recorded before
  business-code edits.
- Acceptance evidence: `docs/development/BASELINE.md`.
- Known limitations: Docker and Compose were unavailable; no user output or
  historical document was deleted.
- Next unblocked tasks: none.

## P0-01 — Git and repository hygiene

- Status: implementation complete; initial signed commit pending.
- Changed files: root/backend/frontend ignore files, `.gitattributes`,
  `.editorconfig`, Docker ignore files, `AGENTS.md`.
- Commands run: `git init -b main`, ignored-file inspection, source-status
  inspection, targeted secret-pattern scan.
- Result: caches, environments, build output, coverage, user outputs, real
  `.env`, dependency directories, and the unverified `backend/de421.bsp` are
  outside the public source boundary.
- Acceptance evidence: `git check-ignore` resolves each protected example to a
  specific ignore rule; the release checker rejects sensitive/generated tracked
  paths.
- Known limitations: no remote exists. Repository owner controls public
  organization, name, and visibility.
- Next unblocked tasks: create the initial DCO-signed local commit; configure a
  remote only with owner authorization.

## P0-02 — Open-source and legal baseline

- Status: local complete; hosted Community Profile pending.
- Changed files: `LICENSE`, `NOTICE`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, `CHANGELOG.md`,
  legal policies, license ADR, fixture license/provenance.
- Commands run: direct dependency inventory, `make audit-licenses`, source
  release-boundary tests.
- Result: Apache-2.0 project licensing, DCO contribution, vulnerability
  reporting, governance, data restrictions, and CC0 synthetic-fixture rules are
  explicit.
- Acceptance evidence: 63 direct dependency licenses accepted; Hippocratic
  licensed `react-leaflet` was unused and removed; `backend/de421.bsp` is
  excluded because redistribution provenance is not proven.
- Known limitations: hosted security-contact identity and GitHub private
  reporting must be set by repository maintainers.
- Next unblocked tasks: generate the actual SPDX SBOM in GitHub Release CI.

## P0-03 — Deterministic test completion

- Status: local complete.
- Changed files: orbit propagation/imaging code and tests, frontend route/login
  tests, `Makefile`.
- Commands run: `make verify` three consecutive times.
- Result: the orbit altitude/azimuth mix-up and incorrect topocentric-vector
  calculation were fixed; all orbit tests use fixed TLE-relative UTC times.
- Acceptance evidence: 96 backend and 6 frontend tests passed three times; each
  backend suite completed in about 28 seconds, under the 120-second gate.
- Known limitations: browser E2E is tracked in P0-12, not counted here.
- Next unblocked tasks: none.

## P0-04 — Replan and contract repair

- Status: local complete.
- Changed files: planning API/schema, `app/services/planning_jobs.py`,
  frontend API/types/modal, backend race/error tests, modal contract test.
- Commands run: targeted replan/API/component tests and full verification.
- Result: background jobs use a new session and immutable captured inputs;
  failures write stable public errors; cancel wins completion races; 25 hours
  rounds to two planning days; one nullable `satellite_id` is used end-to-end.
- Acceptance evidence: normal replace, redacted solver failure with trace log,
  cancel race, already-running/cancelled 409, cross-user non-disclosure, stateless
  parse, and frontend request payload tests pass.
- Known limitations: FastAPI in-process background tasks are explicitly not a
  production durable queue.
- Next unblocked tasks: a durable worker/queue is Phase 1 or later.

## P0-05 — Seed, UTC, and orbit provenance

- Status: local complete.
- Changed files: offline seed, TLE parser, bootstrap, all model datetime
  declarations, initial migration, seed/orbit/model tests.
- Commands run: seed twice without network, bootstrap twice, TLE century tests,
  UTC metadata test, full verification.
- Result: seed inputs are immutable and idempotent; catalog IDs remain strings;
  TLE epochs come from line 1; every SQLAlchemy/Alembic datetime column is
  timezone-aware; CLI seed failures roll back and exit as failures.
- Acceptance evidence: stable two-satellite/four-station seed and stable demo
  organization/constellation/link IDs and counts.
- Known limitations: bundled TLEs are fixed synthetic demonstration inputs, not
  current operational ephemerides.
- Next unblocked tasks: OMM/CDM import is outside Phase 0.

## P0-06 — Error visibility and truthful capability claims

- Status: local complete.
- Changed files: central error envelope/handlers, config safety checks, planner
  status handling, README and architecture text.
- Commands run: typed-error and unknown-exception API tests, lint/type/full
  verification.
- Result: responses include stable error codes and trace IDs without stack
  traces; production rejects demo secrets/mode; documentation describes the
  implemented assignment/overlap/simplified resource constraints.
- Acceptance evidence: known and unknown exception tests pass; repository
  capability text does not claim flight safety or computed Pc.
- Known limitations: the existing solver remains simplified decision support,
  not flight dynamics validation.
- Next unblocked tasks: none.

## P0-07 — Organization and constellation isolation

- Status: implementation and local authorization tests complete; live
  PostgreSQL migration pending P0-12 external CI.
- Changed files: tenancy models/schemas/services/routes, migration `0002`,
  satellite/planning scopes, constellation frontend.
- Commands run: authorization matrix tests, model tests, stateless parse test,
  migration workflow static inspection.
- Result: registration creates a personal organization/default constellation;
  demo has a stable isolated constellation; planner and satellite routes require
  scope; owner/operator/viewer behavior and attach idempotency are enforced.
- Acceptance evidence: cross-tenant, viewer, operator, missing-scope, attach,
  detach, planner-scope, and non-disclosure tests pass.
- Known limitations: upgrade/downgrade/re-upgrade against PostgreSQL is defined
  in CI but not runnable locally without Docker.
- Next unblocked tasks: run GitHub migration job.

## P0-08 — Zero-configuration demo and Compose

- Status: implemented; local Docker acceptance blocked by missing Docker CLI.
- Changed files: Dockerfiles, Compose files, health checks, config, bootstrap,
  `Makefile`, README.
- Commands run: Compose/YAML syntax parsing, offline bootstrap tests, API
  session-to-export test.
- Result: `make demo` requires no `.env`, OpenAI key, or Space-Track account;
  migration/bootstrap gate API start; Redis is optional; demo issues temporary
  tokens; bootstrap is idempotent.
- Acceptance evidence: configuration/bootstrap/API tests pass and Compose
  definitions parse.
- Known limitations: clean-cache five-minute startup, second container start,
  container health, and migration-failure readiness are not observed locally.
- Next unblocked tasks: run the exact P0-08 command sequence on Docker Desktop
  or GitHub Actions.

## P0-09 — Synthetic conjunction replay and evidence

- Status: local complete.
- Changed files: strict demo schemas, CC0 fixture/golden output, replay/evidence
  service, demo API, tests.
- Commands run: fixture hash verifier, golden replay tests, strict-schema tests,
  zero-credential API journey.
- Result: deterministic replay UUID, canonical fixture SHA-256, provenance,
  units, quality degradation, versions, warnings, and limitations are preserved.
  Provided Pc is never labeled as Apex-computed.
- Acceptance evidence: fixture hash above; extra fields are rejected; absent
  covariance degrades quality; Markdown/JSON exports include safety statements.
- Known limitations: no real CDM upload/persistence and no computed Pc.
- Next unblocked tasks: real standards/adapters require a later validated phase.

## P0-10 — Hypothetical unavailable window and planning impact

- Status: local complete.
- Changed files: typed unavailable-window schema, deterministic planning-impact
  service/API/UI/types/tests.
- Commands run: overlap, non-overlap, repeatability, tenancy, and API tests.
- Result: the fixed synthetic task is removed only when the hypothetical window
  overlaps it; before/after sets are stable; runtime metrics are excluded from
  the semantic evidence hash.
- Acceptance evidence: repeat inputs yield the same 64-character SHA-256;
  non-overlap preserves the task and objective; overlap records its filter
  reason; unauthorized constellation/satellite access is rejected.
- Known limitations: this is a scheduling hypothesis, not orbit propagation,
  maneuver generation, or collision-risk recomputation.
- Next unblocked tasks: none.

## P0-11 — User-centered frontend

- Status: implementation and component tests complete; manual browser acceptance
  pending.
- Changed files: demo replay page, constellation page, planner constellation
  selection, login demo entry, API/types/tests.
- Commands run: ESLint, TypeScript, 6 Vitest tests, production build.
- Result: the UI leads with a synthetic/non-operational warning, separately
  explains provided Pc and degraded quality, shows before/after planning impact,
  displays evidence hashes, and offers JSON/Markdown export and feedback.
- Acceptance evidence: login-to-demo, replay safety, impact, replan payload,
  auth store, and protected-route tests pass.
- Known limitations: keyboard-only, WCAG contrast, and 375/768/1440 pixel
  browser checks have not been manually observed.
- Next unblocked tasks: Playwright/manual browser run in P0-12.

## P0-12 — CI, E2E, and supply chain

- Status: workflows implemented; hosted and browser acceptance incomplete.
- Changed files: CI/security/release workflows, Dependabot, API E2E script,
  license and release checkers.
- Commands run: local workflow YAML parse, `make verify`,
  `make audit-licenses`, lockfile offline dry run.
- Result: separate lint/type/unit/build, PostgreSQL migration,
  Compose smoke, source-boundary, secret scan, dependency review, license
  inventory, SPDX SBOM, source archive, and provenance-attestation jobs are
  defined with timeouts.
- Acceptance evidence: local checks pass. The API E2E script covers
  status/session/replay/impact/export against a live demo when available.
- Known limitations: GitHub jobs have not run because no remote exists.
  Playwright browser dependencies could not be installed in this environment,
  so no browser spec is claimed. amd64 CI, real arm64, and WSL2 results are
  pending. Generated SBOM/attestation files do not exist until a Release runs.
- Next unblocked tasks: create/authorize the public remote, run CI, approve
  Playwright dependency installation, and record architecture results.

## P0-13 — Build in Public infrastructure

- Status: local complete; hosted configuration pending.
- Changed files: structured Issue forms, PR template, roadmap, metrics, weekly
  template, validation log, evidence ledger, repository setup checklist.
- Commands run: Issue-form YAML parse and content review.
- Result: public evidence uses E0-E5 behavioral levels and excludes credentials,
  restricted CDM, and copied personal information.
- Acceptance evidence: forms ask for commit/tag, environment, five-minute
  outcome, comprehension, repeat-use intent, and redaction confirmation.
- Known limitations: placeholder owner/repository URLs and GitHub Discussion
  categories require the final public remote.
- Next unblocked tasks: configure the repository checklist after remote creation.

## P0-14 — Public v0.0.x release

- Status: preparation only; not released.
- Changed files: release workflow, changelog, release/source checker, repository
  setup checklist.
- Commands run: release-workflow syntax parse and release-check unit tests.
- Result: a published GitHub Release is configured to create a source archive,
  SPDX SBOM, and artifact attestations, then attach source/SBOM artifacts.
- Acceptance evidence: configuration and source-boundary unit tests pass.
- Known limitations: no tag, public GitHub Release, remote CI result, SBOM,
  provenance attestation, Docker quickstart evidence, or independent-user run
  exists yet. Therefore P0-14 is not complete.
- Next unblocked tasks: complete P0-08/P0-11/P0-12 external gates, then publish
  `v0.0.1` with the fixed release template.

## P0-15 — Six-week market-fit Gate

- Status: not started.
- Dependency: P0-14 plus at least six complete calendar weeks.
- Required evidence: 10 independent demos, 5 structured workflow reports,
  3 user-provided public/synthetic event replays, 2 repeat users after at least
  7 days, 2 relevant-domain contributors, 1 external contribution, at least 90%
  quickstart success, and no unresolved P0/P1 safety issue.
- Current evidence: zero. Maintainer runs, local automation, stars, views, and
  AI-generated feedback do not count.
- Next unblocked tasks: start the public evidence clock only after the first
  runnable release.
