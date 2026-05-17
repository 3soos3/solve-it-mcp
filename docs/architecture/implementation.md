# Implementation Details

Technical notes on the CI/CD pipeline, release process, and multi-platform build architecture.

## CI/CD Workflow Architecture

The repository uses four focused workflows that run in parallel:

### `ci.yml` — Code Quality & Tests (~5 min)

- Ruff linting and formatting
- MyPy type checking
- Pytest with coverage (Python 3.12)
- YAML validation
- Runs on: PRs and main-branch pushes

### `security.yml` — Vulnerability Scanning (~3 min)

- Bandit (Python security linting)
- pip-audit and Safety (dependency vulnerabilities)
- Hadolint (Dockerfile best practices)
- TruffleHog (secret scanning)
- Runs on: PRs, main-branch pushes, and daily scheduled scans

### `docker-pr-validation.yml` — Build Validation (~12 min)

- Single-arch Docker build (`linux/amd64`)
- Health check tests (`/healthz`, `/readyz`)
- Multi-arch build verification
- Trivy security scan
- Runs on: PRs only — does **not** publish images

### `docker-publish.yml` — Production Build (~20 min)

- Multi-arch builds (`linux/amd64`, `linux/arm64`, `linux/arm/v7`)
- SBOM generation (SPDX, CycloneDX)
- Image signing with Cosign (keyless)
- SLSA provenance attestation
- Push to Docker Hub and GHCR
- Runs on: main-branch pushes and git tags only

---

## Release Process

### Version Format

```
v{SOLVE-IT-RELEASE}-{MCP-SHA}
```

Examples:

```
v2025-10-abc1234   # SOLVE-IT release v2025-10, MCP commit abc1234
live-abc1234       # live image, MCP commit abc1234
```

### Creating a Release

```bash
# 1. Ensure main is clean
git checkout main && git pull origin main

# 2. Create an annotated tag
git tag -a v2025-10-0.1.0 -m "Release v2025-10-0.1.0"

# 3. Push tag to trigger the publish workflow
git push origin v2025-10-0.1.0
```

The workflow will:

1. Run full multi-platform security scans
2. Build and push multi-arch images to Docker Hub and GHCR
3. Generate and attach SBOM and Cosign signature
4. Create a GitHub Release with auto-generated notes

### Version Scenarios

| Scenario | Action | Example |
|---|---|---|
| Bug fix | Patch release | `v2025-10-abc1235` |
| New MCP feature | Minor release | `v2025-10-abc1236` |
| SOLVE-IT data update | New release | `v2025-11-abc1237` |
| Breaking change | Major release | `v2025-11-abc1238` |

### Pre-releases

```bash
git tag -a v2025-10-0.1.0-rc.1 -m "Release candidate 1"
git push origin v2025-10-0.1.0-rc.1
```

Pre-releases are automatically marked as pre-releases in GitHub.

---

## Branch Protection

The `main` branch requires the following status checks before merge:

- **CI Summary** (from `ci.yml`)
- **Security Summary** (from `security.yml`)
- **PR Validation Summary** (from `docker-pr-validation.yml`)

Force pushes and direct pushes to `main` are disabled. All changes require a PR.

The `docker-publish.yml` workflow only runs **after** a successful merge to `main`, ensuring no images are built from failing code.

---

## Multi-Platform Build

Images are built for three platforms using QEMU emulation in CI:

| Platform | Notes |
|---|---|
| `linux/amd64` | Native CI build (~5 min) |
| `linux/arm64` | QEMU emulated (~12 min) |
| `linux/arm/v7` | QEMU emulated (~15 min) |

A Docker manifest list bundles all three into a single multi-arch image tag.

### Local Multi-Arch Testing

See [Multi-arch Testing](../development/multiarch-testing.md) for a complete local testing guide.

```bash
# Quick build test for a specific platform
docker buildx build \
  --platform linux/arm64 \
  -t solve-it-mcp:arm64-test \
  -f Dockerfile .
```

---

## Forensic Audit Trail

Every published image is fully traceable:

| Artifact | Location |
|---|---|
| Source commit SHA | `org.opencontainers.image.revision` label |
| Build timestamp | `org.opencontainers.image.created` label |
| SBOM | Attached to GHCR image via Cosign |
| Signature | Attached to GHCR image via Cosign |
| SLSA provenance | Attached to GHCR image via Cosign |
| Workflow run logs | GitHub Actions (retained 90 days) |

Inspect image labels:

```bash
docker inspect ghcr.io/3soos3/solve-it-mcp:latest \
  | jq '.[0].Config.Labels'
```

---

## Related Documentation

- [Security Model](security-model.md)
- [Releases](../development/releases.md)
- [Multi-arch Testing](../development/multiarch-testing.md)
- [Branch Protection](../development/branch-protection.md)
