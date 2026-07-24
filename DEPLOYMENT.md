# Deployment status

The supported Phase 0 path is the local, synthetic Docker Compose demo:

```bash
make demo
```

`docker-compose.prod.yml` is a security-oriented reference, not a production
readiness claim. It disables demo mode, rejects default credentials, runs
migrations before the API, and intentionally uses one API process because the
current FastAPI `BackgroundTasks` planning path is not durable.

Before a real production deployment, the project still needs:

- a durable queue and idempotent worker recovery;
- PostgreSQL backup/restore exercises;
- secrets management and key rotation;
- observability, SLOs and alerting;
- a supported source/licensing path for operational orbit and SSA data;
- threat modeling and an external security review;
- operator approval controls for any later recommendation workflow.

The production reference requires at least:

```bash
export POSTGRES_PASSWORD="$(openssl rand -hex 32)"
export JWT_SECRET="$(openssl rand -hex 32)"
docker compose -f docker-compose.prod.yml up
```

It deliberately exposes no demo session, performs no network seed, uses no LLM,
and must not be described as a flight-safety system. See
[`docs/operations/SUPPORT_MATRIX.md`](docs/operations/SUPPORT_MATRIX.md).
