# Validation metric definitions

| Metric | Definition | Not counted |
| --- | --- | --- |
| Demo start | A successful demo session token issuance | Page view |
| Replay completion | Valid replay result returned and rendered | Button click that errors |
| Explained replay | User correctly distinguishes provided Pc and missing covariance | “Looks good” |
| Impact completion | Before/after comparison returned for a selected constellation asset | Opening the page |
| Evidence export | Successful JSON or Markdown download | Hover/click before replay |
| Time to first value | Start of Quickstart to rendered replay result | Build time reported without user start |
| Setup failure | User cannot reach `/health/ready` or the replay flow | Cosmetic issue after completion |
| Return use | Same consenting participant completes a workflow in another week | Refresh during one session |

## Six-week Gate

At the end of six complete calendar weeks, record one of:

- `GO`: repeated problem evidence and successful workflows justify Phase 1.
- `ITERATE`: problem exists but workflow or trust model needs another test.
- `PIVOT`: adjacent problem has stronger evidence.
- `STOP EXPANSION`: evidence does not justify more capability.

The exact numeric thresholds and required evidence are defined in
`PHASE0_AI_EXECUTION_PLAN.md` P0-15. Do not backfill or fabricate missing weeks.
