# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2025-10-0.1.0] - 2026-02-24

**SOLVE-IT Knowledge Base**: v0.2025-10  
**MCP Server Version**: 0.1.0

### Attribution

This release is based on a fork of the original [solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) created by **CKE-Proto (L3K-A)** and licensed under MIT.

This fork has been significantly enhanced with production-ready features while maintaining the original MIT license and proper attribution to the original author.

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

### Added
- **Comprehensive documentation site** with MkDocs Material
  - Deployed to GitHub Pages at https://3soos3.github.io/solve-it-mcp/
  - Persona-specific guides for forensic analysts and researchers
  - Complete getting started guide with tabbed options
  - Troubleshooting guide with common issues and solutions
  - Integration examples and use cases
- **Automated documentation deployment** via GitHub Actions
- **Requirements management** with pip-tools for reproducible builds
- **Documentation badge** in README linking to docs site

### Changed
- **Documentation restructure**: Organized into logical categories
  - `docs/architecture/` - Implementation and security details
  - `docs/deployment/` - Docker and Kubernetes guides
  - `docs/development/` - Contributing, testing, and releases
  - `docs/guides/` - User-focused tutorials and troubleshooting
  - `docs/reference/` - API and tool references (coming soon)
- **README.md**: Condensed from 577 to ~200 lines with clear navigation to comprehensive docs
- **Documentation references**: Updated all cross-references to new structure
- **Makefile**: Added docs-serve and docs-build commands

### Fixed
- **Cross-references**: Updated all internal documentation links
  - `.github/workflows/docker-publish.yml` → `docs/deployment/docker.md`
  - `.github/workflows/zenodo-publish.yml` → new doc paths
  - `docs/development/releases.md` → fixed MULTIARCH_TESTING link
  - `examples/k8s/README.md` → updated documentation links

---

[0.2025-10-0.1.0]: https://github.com/3soos3/solve-it-mcp/releases/tag/v0.2025-10-0.1.0
