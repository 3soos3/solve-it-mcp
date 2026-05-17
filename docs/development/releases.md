# Release Process

How to create and publish a new release of SOLVE-IT MCP Server.

## Version Format

```
v{SOLVE-IT-RELEASE}-{MCP-SHA}
```

| Image type | Tag format | Example |
|---|---|---|
| `:release` | `<solve-it-release>-<mcp-sha>` | `v2025-10-abc1234` |
| `:latest` | `<solve-it-sha>-<mcp-sha>` | `def5678-abc1234` |
| `:live` | `live-<mcp-sha>` | `live-abc1234` |

## Creating a Release

### Prerequisites

- All tests passing on `main`
- No known CRITICAL/HIGH security vulnerabilities
- CHANGELOG updated

### Step-by-Step

**1. Ensure main is clean:**

```bash
git checkout main
git pull origin main
git status  # should be clean
```

**2. Create an annotated tag:**

```bash
git tag -a v2025-10-0.1.0 -m "Release v2025-10-0.1.0

SOLVE-IT Knowledge Base: v2025-10
MCP Server: 0.1.0

Changes:
- List key changes
"
```

**3. Push the tag:**

```bash
git push origin v2025-10-0.1.0
```

**4. Monitor the build:**

Go to: https://github.com/3soos3/solve-it-mcp/actions

The workflow will:

1. Run full 3-platform security scans (parallel, ~12 min)
2. Build multi-arch images and push to Docker Hub + GHCR (~12 min)
3. Generate SBOM and sign images with Cosign
4. Create a GitHub Release with auto-generated notes

**Total: ~24 minutes**

**5. Verify:**

```bash
# Check Docker Hub
docker pull 3soos3/solve-it-mcp:v2025-10-0.1.0
docker run --rm -d -p 8000:8000 3soos3/solve-it-mcp:v2025-10-0.1.0
curl http://localhost:8000/healthz

# Verify multi-arch manifest
docker manifest inspect 3soos3/solve-it-mcp:v2025-10-0.1.0

# Verify GHCR signature
cosign verify ghcr.io/3soos3/solve-it-mcp:v2025-10-0.1.0 \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

---

## Pre-Releases

```bash
# Release candidate
git tag -a v2025-10-0.1.0-rc.1 -m "Release candidate 1"
git push origin v2025-10-0.1.0-rc.1
```

Tags containing `-rc`, `-beta`, or `-alpha` are automatically marked as pre-releases on GitHub.

---

## Version Scenarios

### Security patch

```
Current: v2025-10-abc1234
Fix: Update vulnerable dependency
Action: Push a new commit, tag as v2025-10-abc1235
```

### New feature

```
Current: v2025-10-abc1234
Feature: New MCP tool
Action: Push a new commit, tag as v2025-10-abc1235
```

### SOLVE-IT data update

```
Current: v2025-10-abc1234
Update: SOLVE-IT releases v2025-11
Action: Tag as v2025-11-abc1235
(Data is fetched automatically from the new release tag during build)
```

---

## Rollback

Prefer creating a patch release:

```bash
# Fix issue on main
git commit -m "fix: critical issue"
git push origin main

git tag -a v2025-10-abc1236 -m "Hotfix"
git push origin v2025-10-abc1236
```

To delete a bad tag:

```bash
git tag -d v2025-10-abc1234
git push origin :refs/tags/v2025-10-abc1234
```

---

## After Release: Helm Chart Update

```bash
cd ~/solve-it-charts

# Update Chart.yaml appVersion and values.yaml image.tag
git commit -am "Update to SOLVE-IT MCP v2025-10-abc1234"
git push origin main
```

---

## Related Documentation

- [Branch Protection](branch-protection.md)
- [Multi-arch Testing](multiarch-testing.md)
- [Docker Deployment](../deployment/docker.md)
