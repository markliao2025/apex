# Phase 0 execution log

Last updated: 2026-07-25 (Asia/Shanghai)

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
| P0-08 | Hosted acceptance complete | The zero-configuration Compose path passed on a clean GitHub-hosted Linux Docker runner; Docker remains unavailable on this workstation. |
| P0-09 to P0-10 | Local complete | Synthetic replay, evidence, hypothetical unavailable window, stable planning diff, and semantic hash are verified. |
| P0-11 | Local and hosted complete | Keyboard, responsive, safety-copy, evidence-export, and clean-console browser acceptance pass locally and in hosted Linux Chromium. |
| P0-12 | Hosted acceptance complete | CI, PostgreSQL migration, Compose/API/Playwright E2E, secret/dependency/license scans, CodeQL, and PR SPDX SBOM generation pass on GitHub. Release attestation remains a P0-14 gate. |
| P0-13 | Hosted setup complete | Public Issues, Discussions, security reporting, build-in-public forms, roadmap, metrics, and evidence ledger are live; the single-maintainer risk is recorded. |
| P0-14 | Release-candidate preparation only | The public repository and a green launch PR exist, but no tag, GitHub Release, release attestation, or public evidence-clock start has been produced. |
| P0-15 | Not started | Requires P0-14 plus six full calendar weeks and independent-user evidence. |

## Verification snapshot

- `make verify` passed after the hosted launch fixes on 2026-07-25.
- Current gate: Ruff and ESLint pass; Mypy passes for 57 source files;
  application and E2E TypeScript pass; 102 backend tests and 11 frontend tests
  pass; the frontend production build passes.
- The committed Playwright Chromium journey passes in Google Chrome
  150.0.7871.184 on macOS 26.5.2 arm64. It covers keyboard-only Demo entry,
  replay, provided-Pc and missing-covariance explanation, planning impact,
  JSON/Markdown export contents, clean console/network, and 375/768/1440-pixel
  widths without horizontal overflow.
- Backend line coverage: 78%.
- Synthetic fixture SHA-256:
  `a45d60780bbf80e7ef56b528358136747eb4755de362daf37a9d7bff78dce188`.
- `make audit-licenses`: 62 installed direct Python/Node packages are accepted.
- The npm high/critical policy rejects every unlisted advisory. A temporary
  exception for `GHSA-qwww-vcr4-c8h2` is limited to `react-router` and
  `react-router-dom`, documents that Apex has no RSC/server-action/SSR path, and
  expires on 2026-08-08.
- GitHub PR checks for commit `f725b7d` passed: verify, PostgreSQL
  upgrade/downgrade/re-upgrade, Compose/API smoke, Linux Chromium Playwright,
  dependency review, secret scan, supply-chain/license/npm policy, and Python
  and JavaScript/TypeScript CodeQL.
- The passing Security workflow produced a non-empty `apex-sbom` SPDX artifact.
- Workflow, Issue-form, and Compose YAML files passed local syntax parsing.
- Expected dependency warnings remain: `passlib` uses Python's deprecated
  `crypt`, and Starlette warns that its legacy `httpx` TestClient integration
  will move to `httpx2`. They do not fail Phase 0.

## P0-00 — Baseline and safety

- Status: local complete.
- Implementation commit:
  `7acfe70df7c7f0411e0ba2ff301ca460bf8c0656` (DCO signed).
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

- Status: local complete.
- Changed files: root/backend/frontend ignore files, `.gitattributes`,
  `.editorconfig`, Docker ignore files, `AGENTS.md`.
- Commands run: `git init -b main`, ignored-file inspection, source-status
  inspection, targeted secret-pattern scan, staged-source check, DCO-signed
  initial commit.
- Result: caches, environments, build output, coverage, user outputs, real
  `.env`, dependency directories, and the unverified `backend/de421.bsp` are
  outside the public source boundary.
- Acceptance evidence: `git check-ignore` resolves each protected example to a
  specific ignore rule; the release checker rejects sensitive/generated tracked
  paths.
- Known limitations: the public repository has one maintainer, recorded as a
  continuity risk.
- Next unblocked tasks: add a second trusted maintainer before claiming
  production support.

## P0-02 — Open-source and legal baseline

- Status: local complete; public repository configuration complete.
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
- Known limitations: the project currently has one maintainer.
- Next unblocked tasks: publish and attest the release SPDX SBOM in P0-14.

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

- Status: implementation, authorization tests, and hosted PostgreSQL migration
  acceptance complete.
- Changed files: tenancy models/schemas/services/routes, migration `0002`,
  satellite/planning scopes, constellation frontend.
- Commands run: authorization matrix tests, model tests, stateless parse test,
  migration workflow static inspection.
- Result: registration creates a personal organization/default constellation;
  demo has a stable isolated constellation; planner and satellite routes require
  scope; owner/operator/viewer behavior and attach idempotency are enforced.
- Acceptance evidence: cross-tenant, viewer, operator, missing-scope, attach,
  detach, planner-scope, and non-disclosure tests pass. GitHub job
  `postgres-migration` passed upgrade, downgrade to `0001_initial`, and
  re-upgrade after adding a regression test for the literal `:default` suffix.
- Known limitations: the live migration was exercised on hosted amd64 Linux,
  not this Docker-less arm64 workstation.
- Next unblocked tasks: none for Phase 0.

## P0-08 — Zero-configuration demo and Compose

- Status: hosted Docker acceptance complete; local Docker remains unavailable.
- Changed files: Dockerfiles, Compose files, health checks, config, bootstrap,
  `Makefile`, README.
- Commands run: Compose/YAML syntax parsing, offline bootstrap tests, API
  session-to-export test.
- Result: `make demo` requires no `.env`, OpenAI key, or Space-Track account;
  migration/bootstrap gate API start; Redis is optional; demo issues temporary
  tokens; bootstrap is idempotent.
- Acceptance evidence: configuration/bootstrap/API tests pass; the GitHub
  `compose-smoke` job built the images, reached healthy API/frontend, verified
  demo readiness, and completed the documented live API journey in 83 seconds.
- Known limitations: second-start timing and WSL2 remain unobserved; hosted
  clean Linux Docker and local arm64 browser evidence are recorded separately.
- Next unblocked tasks: collect optional WSL2 portability evidence.

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

- Status: local and hosted browser acceptance complete.
- Changed files: demo replay page, constellation page, planner constellation
  selection, login demo entry, responsive layout, API/types/tests.
- Commands run: ESLint, TypeScript, 11 Vitest tests, production build, local
  Playwright Chromium journey, and visual inspection of generated desktop,
  tablet, and mobile screenshots.
- Result: the UI leads with a synthetic/non-operational warning, separately
  explains provided Pc and degraded quality, shows before/after planning impact,
  displays evidence hashes, and offers JSON/Markdown export and feedback. The
  anonymous auth probe/reload loop, missing local CORS policy, narrow email
  field, unnamed password control, unassociated labels, and mobile header
  overflow found during browser acceptance are fixed.
- Acceptance evidence: login-to-demo, replay safety, impact, replan payload,
  auth store, protected-route, responsive navigation, and selector-label tests
  pass. A keyboard-only user can activate Demo with Enter; both evidence formats
  contain the not-flight-certified, no-maneuver, provided/not-computed, and hash
  statements; console errors and request failures are empty; 375, 768, and 1440
  pixel widths do not overflow.
- Known limitations: maintainer automation does not substitute for
  independent-user comprehension evidence.
- Next unblocked tasks: collect public-user evidence after P0-14.

## P0-12 — CI, E2E, and supply chain

- Status: hosted PR acceptance complete.
- Changed files: CI/security/release workflows, Dependabot, API E2E script,
  Playwright configuration/journey, license and release checkers.
- Commands run: local workflow YAML parse, `make verify`,
  `make audit-licenses`, lockfile offline dry run, Playwright against a live
  local demo, the strict expiring npm advisory policy, and all hosted CI and
  Security jobs.
- Result: separate lint/type/unit/build, PostgreSQL migration,
  Compose smoke, Playwright browser journey, source-boundary, secret scan,
  dependency review, npm advisory, license inventory, SPDX SBOM, source archive,
  and provenance-attestation jobs are defined with timeouts.
- Acceptance evidence: local checks pass. The API E2E script covers
  status/session/replay/impact/export against a live demo; the Playwright spec
  covers keyboard entry, safety semantics, constellation scope, replay, impact,
  both exports, console/network failures, and responsive overflow. All required
  checks passed on PR #21, and the Security workflow uploaded `apex-sbom`.
- Known limitations: hosted results cover amd64 Linux; WSL2 is pending. The PR
  SBOM is a retained workflow artifact, not the release artifact or attestation.
- Next unblocked tasks: land the green PR if needed, then run the P0-14 release
  workflow.

## P0-13 — Build in Public infrastructure

- Status: hosted configuration complete.
- Changed files: structured Issue forms, PR template, roadmap, metrics, weekly
  template, validation log, evidence ledger, repository setup checklist.
- Commands run: Issue-form YAML parse and content review.
- Result: public evidence uses E0-E5 behavioral levels and excludes credentials,
  restricted CDM, and copied personal information.
- Acceptance evidence: forms ask for commit/tag, environment, five-minute
  outcome, comprehension, repeat-use intent, and redaction confirmation.
- Known limitations: one maintainer is a continuity risk; no independent-user
  evidence exists yet.
- Next unblocked tasks: use the live Issues and Discussions during P0-14/P0-15.

## P0-14 — Public v0.0.x release

- Status: preparation only; not released.
- Changed files: release workflow, changelog, release/source checker, repository
  setup checklist.
- Commands run: release-workflow syntax parse and release-check unit tests.
- Result: a published GitHub Release is configured to create a source archive,
  SPDX SBOM, and artifact attestations, then attach source/SBOM artifacts.
- Acceptance evidence: configuration and source-boundary unit tests pass.
- Known limitations: no tag, public GitHub Release, release provenance
  attestation, or independent-user run exists yet. Therefore P0-14 is not
  complete.
- Public-repository preflight on 2026-07-25:
  - <https://github.com/markliao2025/apex> is public with Issues, Discussions,
    private vulnerability reporting, secret scanning/push protection,
    Dependabot security updates, and read-only default Actions permissions.
  - PR #21 is mergeable and all 10 observed checks pass, including clean
    Compose/API startup, PostgreSQL migration, Linux browser E2E, supply-chain
    policy, secret scanning, dependency review, and CodeQL.
  - The Security run produced the non-empty `apex-sbom` artifact; release
    source/SBOM attachments and attestations still require a published tag.
  - `main` requires PRs and the nine named CI/security contexts, uses strict
    up-to-date checks and linear history, and disallows force-pushes/deletion.
    Approval count is zero because the single maintainer cannot independently
    approve their own PR.
  - No tag, Release, release attestation, or public evidence-clock entry was
    created during repository launch.
- Next unblocked tasks: land PR #21 if needed, then publish `v0.0.1` only
  through the configured release workflow and start the evidence clock from
  that date.

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
