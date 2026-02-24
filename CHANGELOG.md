# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-24

### Added
- **Production-ready CI/CD workflows** with parallel execution
  - Separate workflows for code quality, security, and Docker builds
  - Faster feedback (~12 min vs 25 min)
- **License compliance checking** (blocks GPL/AGPL dependencies)
- **OpenSSF Scorecard** integration for security best practices
- **Automated NOTICE file** generation for dependency attribution
- **Dual registry publishing**: Docker Hub (clean) + GHCR (forensic artifacts)
- **SBOM generation** in multiple formats (SPDX, CycloneDX, Syft)
- **Image signing** with Cosign (keyless) on GHCR
- **Security policy** (SECURITY.md) with vulnerability reporting
- **Comprehensive documentation** for Docker, Kubernetes, and forensic verification

### Changed
- **CodeQL Action** updated from v3 to v4 (v3 deprecated)
- **Multi-arch Docker builds** now only on main (PRs build AMD64 only for speed)
- **Security scans** made non-blocking (report issues without failing builds)

### Fixed
- **OpenSSF Scorecard** no longer tries to publish for fork repositories
- **License compliance** creates PRs instead of direct pushes (respects branch protection)
- **NOTICE file** timestamp removed to prevent infinite PR loop
- **YAML linting** errors (trailing spaces) in all workflow files
- **Hadolint** adjusted to error-only threshold

### Security
- All Docker images include SBOM and provenance attestations
- Cryptographic signatures available on GHCR images
- Automated vulnerability scanning (Trivy, Bandit, Safety, pip-audit)
- Secret scanning with TruffleHog

## [Unreleased]
- Future enhancements will be listed here

---

[0.1.0]: https://github.com/3soos3/solve-it-mcp/releases/tag/v0.1.0
