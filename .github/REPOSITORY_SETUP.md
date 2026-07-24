# GitHub repository launch checklist

These settings require repository-owner/admin access and cannot be safely
guessed by an implementation Agent.

- Repository: <https://github.com/markliao2025/apex>
- Public repository created: 2026-07-25 (Asia/Shanghai)
- Launch maintainer state: one maintainer (`markliao2025`). This is explicitly
  recorded as a continuity risk. Add a second trusted maintainer before claiming
  production support or depending on repository-owner availability.

- [x] Replace `OWNER/REPOSITORY` in `.github/ISSUE_TEMPLATE/config.yml`.
- [x] Set the repository description and topics (`space-situational-awareness`,
      `satellite-planning`, `fastapi`, `open-source`).
- [x] Enable Issues and Discussions.
- [x] Enable private vulnerability reporting.
- [ ] Protect `main`: require PR, CI, migration, and security checks.
- [x] Enable secret scanning and push protection.
- [x] Confirm default token permissions are read-only.
- [x] Configure Dependabot security updates.
- [x] Add at least two maintainers or document the single-maintainer risk.
- [ ] Run `make demo` on a clean Docker-capable host.
- [x] Run `make release-check`.
- [ ] Confirm the Security workflow produced a secret-scan result and SPDX SBOM.
- [ ] Confirm a published Release contains an attested source archive and SPDX SBOM.
- [ ] Confirm `backend/de421.bsp`, `.env`, `outputs/`, generated files, and
      local user content are absent from the release.
- [ ] Publish `v0.0.1` only after clean Compose and live E2E pass.
- [ ] Start the six-week evidence clock on the public release date; do not
      backdate P0-15.
