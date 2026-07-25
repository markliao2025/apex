# Third-party assets and release inventory

| Asset | Source | License/terms | Redistributable | SHA-256 | Release action |
|---|---|---|---:|---|---|
| `backend/de421.bsp` | Undocumented at baseline | Unverified | No, until proven | `a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc` | Exclude from public image/release |
| Synthetic conjunction fixture | Created for Apex | CC0-1.0 | Yes | `a45d60780bbf80e7ef56b528358136747eb4755de362daf37a9d7bff78dce188` (canonical event JSON) | Include |
| Synthetic demo TLE inputs | Created/modified for Apex software demonstration; not an operational catalog | CC0-1.0 under repository fixture/data policy | Yes | Source-controlled text | Include with non-operational warning |
| `docs/assets/apex-phase0-dark-interface.png` | Generated for Apex with OpenAI ImageGen; original prompt requested a dark Phase 0 SSA workbench concept with synthetic/provided-Pc and non-flight-certified labels; no third-party input image | Repository Apache-2.0 terms | Yes | `d6bdfaaf7fe06f2b38ea32bd977b2cee384b37d235ff137347afc0beefb5832d` | Include as a clearly labelled concept view, not a product screenshot |
| Leaflet | npm dependency | BSD-2-Clause | Yes under its terms | Lockfile-managed | Include notices through dependency inventory |
| Skyfield | Python dependency | MIT | Yes under its terms | Lockfile-managed | Include notices through dependency inventory |
| SGP4 | Python dependency | MIT | Yes under its terms | Lockfile-managed | Include notices through dependency inventory |

This table is a release control, not legal advice. Lock files are the current version
inventory. `make audit-licenses` blocks direct dependencies with missing licenses or
AGPL/SSPL/BUSL/Commons-Clause/Elastic/Hippocratic restrictions. The GitHub Release
workflow is configured to generate and attest an SPDX SBOM; it is not release evidence
until that artifact exists on a published release.

`react-leaflet@4.2.1` was removed before the initial source release because its
declared `Hippocratic-2.1` license is not part of the project's accepted open-source
dependency policy. The existing map uses Leaflet directly, so removal changes no
user-visible capability.
