# Future Agent design contract

Phase 0 intentionally ships no LLM Agent. This document fixes the trust and tool
boundaries that later Agent work must respect.

## User job

The Agent should help an operator answer:

1. What evidence is available and how trustworthy is it?
2. Which conjunctions or planning conflicts need human attention first?
3. What assumptions changed the schedule?
4. Which missing datum or approval blocks the next decision?

It must not pretend to be an autonomous spacecraft operator.

## Architecture

```text
User
  -> Agent coordinator (reasoning + state machine)
      -> read-only evidence tools
      -> deterministic analysis tools
      -> planning what-if tools
      -> approval gateway
  -> cited answer / proposed action
  -> human accepts, edits, or rejects
```

The coordinator never receives database credentials and never writes arbitrary
SQL. Every tool performs its own user/organization/constellation authorization.

## Tool contracts

| Tool | Mutability | Required scope | Output requirement |
| --- | --- | --- | --- |
| `list_constellations` | Read | current user | role and stable IDs |
| `get_constellation_assets` | Read | constellation membership | catalog ID, orbit provenance and age |
| `get_conjunction_evidence` | Read | authorized event | source, frame, units, timestamps and quality |
| `replay_conjunction` | Deterministic read/compute | event | input hash, method/version, warnings |
| `compute_pc` | Compute, Phase 1+ only | covariance + approved method | computed label, method/version, sensitivity |
| `compare_planning_impact` | Deterministic what-if | constellation + event | before/after, assumptions, `physics_verified` |
| `draft_operator_note` | Local draft | authorized evidence | citations and unresolved questions |
| `propose_mitigation` | Proposal only | human-approved analysis | no command, explicit approval required |

No general shell, filesystem, HTTP fetch, SQL, credential, or command-sending
tool is allowed.

## State machine

```text
collect evidence
  -> validate provenance/units/time/frame
  -> classify data quality
  -> analyze/replay
  -> compare planning consequences
  -> explain uncertainty
  -> request human approval
  -> export evidence
```

Any failed validation enters `blocked`, with a typed reason and a user action.
The Agent may not silently substitute data, covariance, reference frames or
time systems.

## Approval policy

- Read-only listing and replay can run without per-call confirmation after the
  user selects a scope.
- Attaching/removing constellation assets requires normal product authorization.
- External data import requires source/terms preview and explicit confirmation.
- Any maneuver proposal, external message, task deployment or command requires a
  named human approver and a separate execution system.
- Phase 0/1/2 never exposes a command-execution tool.

## Memory and audit

Conversation memory is not authoritative mission state. Durable Agent runs must
store:

- actor and organization/constellation scope;
- tool name/version and normalized arguments;
- input evidence hashes and provenance;
- outputs, typed errors and trace IDs;
- approvals and rejected proposals;
- model/provider version where an LLM was used.

Secrets, raw restricted messages and bearer tokens must never be written to the
audit narrative.

## Evaluation before launch

- cross-tenant prompt-injection tests;
- tool-argument authorization tests;
- unsupported-claim and hallucinated-Pc tests;
- unit/reference-frame/time-system adversarial cases;
- missing-covariance and stale-orbit cases;
- deterministic replay equivalence;
- human-approval bypass attempts;
- red-team tests using untrusted event text.

Agent work starts only after Phase 0 external evidence shows users need help
orchestrating these tools. It is not justified merely because an LLM can be
connected.
