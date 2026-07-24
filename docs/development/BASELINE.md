# Phase 0 engineering baseline

Recorded: 2026-07-24  
Machine: macOS 26.5.2, arm64  
Scope: P0-00 read-only baseline before Phase 0 implementation

## Runtime and repository state

| Item | Result |
|---|---|
| Git | Not a Git worktree at baseline |
| Python used by backend venv | 3.12.13 |
| System Python | 3.9.6 |
| Node.js | 25.3.0 |
| npm | 11.7.0 |
| Docker CLI | Not installed or not on PATH |
| Backend Python files | 44 |
| Backend test files | 7 |
| Frontend TypeScript files | 14 |

## Baseline checks

| Check | Command | Result | Duration |
|---|---|---|---:|
| Backend lint | `backend/.venv/bin/ruff check backend` | 72 findings, 66 auto-fixable | 1s |
| Backend type check | `backend/.venv/bin/mypy backend/app` | No output after 60s; manually interrupted | >60s |
| Backend tests | `backend/.venv/bin/pytest` | 58 passed, 4 warnings, 66% coverage | 23.59s |
| Frontend lint | `npm run lint` | 4 errors, 2 warnings | 5s |
| Frontend type/build | `npm run build` | Passed | 8s |
| Frontend tests | `npm run test` | Failed: no test files | 2s |

The first health score was 3.7/10. The score is intentionally conservative: a passing
backend suite does not compensate for absent frontend tests, 78 combined lint findings,
and a type checker without a bounded completion time.

## Confirmed Phase 0 defects

1. Satellite and planner queries are not scoped to an organization or constellation.
2. Replan captures and reassigns `req` inside the same closure, then swallows the error.
3. Cancel can be overwritten by a background planning task.
4. Seed mutates shared dictionaries and stores execution time as TLE epoch.
5. FastAPI error responses do not match the documented envelope.
6. Planner documentation claims physical constraints that are only approximations.
7. Frontend and backend disagree about planned-task and replan types.
8. Default Compose requires a local `.env` and manual migration/seed.
9. The repository has no open-source license or community files.
10. The repository contains generated output and an unverified binary asset.

## Local-only and generated material

The following existed before Git initialization and must not be included in source:

- `backend/.env`
- `backend/.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/htmlcov/`
- Python `__pycache__/`
- `*.tsbuildinfo`
- `outputs/`

No generated directory was deleted during P0-00.

## Binary asset

`backend/de421.bsp`

- Size: 16,788,480 bytes
- SHA-256: `a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc`
- Provenance at baseline: not documented
- Release decision: excluded from public release until provenance is documented

## Verification limitation

Docker is unavailable on this machine. Compose and Dockerfile changes can be statically
validated, but the clean-container Quickstart Gate must be run on a Docker-capable
macOS/Linux/CI host before a public release.

