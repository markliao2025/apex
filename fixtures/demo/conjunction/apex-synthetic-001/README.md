# APEX-SYNTHETIC-001

This is a deliberately synthetic conjunction event for deterministic testing
and product demonstration. It is not an operational alert.

- `collision_probability` is an input supplied by the fixture.
- Apex does not compute Pc in Phase 0.
- Covariance is absent, so Pc cannot be independently reproduced.
- No avoidance maneuver or post-maneuver trajectory is generated.
- Six-digit catalog IDs are strings to prevent truncation and future schema
  assumptions.

The canonical fixture hash is SHA-256 over UTF-8 JSON serialized with sorted
keys and separators `,` and `:` (no insignificant whitespace).
