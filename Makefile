SHELL := /bin/sh

BACKEND_BIN ?= backend/.venv/bin
PYTEST := $(BACKEND_BIN)/pytest
RUFF := $(BACKEND_BIN)/ruff
MYPY := $(BACKEND_BIN)/mypy
DEMO_VOLUME := apex_phase0_demo_pgdata

.PHONY: help demo dev down logs verify test test-backend test-frontend \
	lint typecheck test-e2e audit-licenses reset-demo release-check migrate seed

help: ## Show supported commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

demo: ## Build and start the zero-configuration synthetic demo
	docker compose up --build

dev: demo ## Alias for demo

down: ## Stop the demo while preserving its named database volume
	docker compose down

logs: ## Follow demo logs
	docker compose logs -f

test: test-backend test-frontend ## Run all non-browser tests without network

test-backend: ## Run backend tests with a 120-second suite timeout
	cd backend && perl -e 'alarm 120; exec @ARGV' ./.venv/bin/pytest

test-frontend: ## Run frontend unit/component tests
	cd frontend && npm run test

lint: ## Run backend and frontend linters
	cd backend && ./.venv/bin/ruff check .
	cd frontend && npm run lint

typecheck: ## Run Python and TypeScript type checks
	cd backend && ./.venv/bin/mypy app
	cd frontend && npx tsc -b

verify: lint typecheck test ## Run the local release quality gate
	cd frontend && npm run build
	$(BACKEND_BIN)/python scripts/verify_fixture.py

test-e2e: ## Run the live session-to-impact journey against a running demo
	$(BACKEND_BIN)/python scripts/e2e_demo.py

audit-licenses: ## Enforce the direct-dependency open-source license policy
	$(BACKEND_BIN)/python scripts/audit_licenses.py

reset-demo: ## Remove only the named Phase 0 demo database volume
	@echo "Removing Docker demo volume: $(DEMO_VOLUME)"
	docker compose down --volumes

release-check: verify audit-licenses ## Check release docs, licenses, fixture integrity, and source boundary
	$(BACKEND_BIN)/python scripts/release_check.py

migrate: ## Apply database migrations in the running API container
	docker compose exec api alembic upgrade head

seed: ## Re-run deterministic offline demo bootstrap
	docker compose exec api python -m app.scripts.bootstrap_demo
