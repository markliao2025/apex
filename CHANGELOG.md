# Changelog

All notable changes will be documented here. The project follows Semantic Versioning
once tagged releases begin.

## Unreleased

### Added

- Playwright coverage for the keyboard-driven synthetic replay, evidence exports,
  clean console, and 375/768/1440-pixel responsive checks.
- A dedicated browser E2E GitHub Actions job with failure artifacts.

### Fixed

- Allowlisted local frontend origins so the documented browser demo can call the
  API without disabling CORS.
- Prevented anonymous `/auth/me` checks and the resulting 401 login reload loop.
- Made the login controls, replay selectors, primary navigation, and logout
  action explicitly labelled and keyboard accessible.
- Removed mobile header overflow while preserving constellation management,
  planning, and risk replay navigation.

### Security

- Updated Axios, React Router, Vitest, and affected transitive development
  dependencies; `npm audit` reports zero known vulnerabilities.

## 0.0.1 - 2026-07-24

### Added

- Phase 0 product and AI-executable implementation plans.
- Apache-2.0 license and open-source community baseline.
- Organization and constellation isolation for all planning assets.
- Deterministic offline demo bootstrap and synthetic conjunction replay.
- Provided-Pc and covariance-quality labels with canonical fixture hash.
- Hypothetical planning-impact comparison and JSON/Markdown evidence export.
- User-centered constellation management and three-step replay UI.
- Local verification, release checks, CI scaffolding, and Build in Public templates.

### Changed

- Phase 0 is explicitly limited to synthetic replay, provided Pc, and hypothetical
  planning impact.

### Security

- Local secrets and generated artifacts are excluded from source control.
