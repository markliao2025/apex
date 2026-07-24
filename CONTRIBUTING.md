# Contributing to Apex

Thanks for helping build an auditable, local-first conjunction decision workbench.

## Before opening code

1. Read `SSA_OPEN_SOURCE_PRODUCT_AND_DEVELOPMENT_PLAN.md`.
2. Read `PHASE0_AI_EXECUTION_PLAN.md`.
3. Do not add real or restricted CDM, Space-Track credentials, operational secrets, or
   data you cannot redistribute.
4. Open an issue before changing risk semantics, reference frames, units, approval
   boundaries, or public API contracts.

## Development

```bash
make demo
make verify
```

The default path must work without OpenAI, Space-Track, or other private credentials.

## Pull requests

- Keep one behavior change per PR.
- Add a failing test before the implementation when fixing a bug.
- Document units, time systems, reference frames, provenance, and limitations.
- Update the changelog for user-visible behavior.
- Never label an input-provided probability as computed by Apex.
- Do not add shell, arbitrary SQL, or command execution to Agent-facing tools.

## Developer Certificate of Origin

This project uses the Developer Certificate of Origin 1.1. Sign every commit:

```bash
git commit -s
```

The sign-off certifies that you have the right to submit the contribution under the
project license. Read the full DCO at https://developercertificate.org/.

## Reporting security issues

Do not file public issues for vulnerabilities or sensitive data exposure. Follow
`SECURITY.md`.

