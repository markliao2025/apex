# GitHub repository launch checklist

These settings require repository-owner/admin access and cannot be safely
guessed by an implementation Agent.

- [ ] Replace `OWNER/REPOSITORY` in `.github/ISSUE_TEMPLATE/config.yml`.
- [ ] Set the repository description and topics (`space-situational-awareness`,
      `satellite-planning`, `fastapi`, `open-source`).
- [ ] Enable Issues and Discussions.
- [ ] Enable private vulnerability reporting.
- [ ] Protect `main`: require PR, CI, migration, and security checks.
- [ ] Enable secret scanning and push protection.
- [ ] Confirm default token permissions are read-only.
- [ ] Configure Dependabot security updates.
- [ ] Add at least two maintainers or document the single-maintainer risk.
- [ ] Run `make demo` on a clean Docker-capable host.
- [ ] Run `make release-check`.
- [ ] Confirm the Security workflow produced a secret-scan result and SPDX SBOM.
- [ ] Confirm a published Release contains an attested source archive and SPDX SBOM.
- [ ] Confirm `backend/de421.bsp`, `.env`, `outputs/`, generated files, and
      local user content are absent from the release.
- [ ] Publish `v0.0.1` only after clean Compose and live E2E pass.
- [ ] Start the six-week evidence clock on the public release date; do not
      backdate P0-15.
