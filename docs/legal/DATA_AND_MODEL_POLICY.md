# Data and model policy

## Default behavior

Apex Phase 0 runs offline with repository-owned synthetic fixtures. No Space-Track,
CelesTrak, LLM, telemetry, or private API is required.

## Restricted or user-provided data

- Do not commit Space-Track credentials or downloaded restricted messages.
- Do not submit real CDM unless you have explicit permission to share it.
- Logs must not contain raw credentials, bearer tokens, or restricted message bodies.
- Future Space-Track support is bring-your-own-credentials and stores data locally.

## CelesTrak

Future adapters must cache responses, request only needed data, stop on service 50x
responses, and follow the current CelesTrak usage policy. Phase 0 does not fetch it.

## LLM providers

LLM integration is optional and disabled in Phase 0. External models must never receive
restricted orbit messages unless the operator has explicitly configured and approved
that data flow.

## Generated outputs

Generated reports inherit neither a claim of flight certification nor rights to their
input data. Each report carries provenance, limitations, and an evidence hash.

