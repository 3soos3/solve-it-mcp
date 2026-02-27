# Release Process Documentation

This document describes the release process for the SOLVE-IT MCP Server.

## Version Numbering Scheme

### Format

```
v{SOLVEIT_VERSION}-{MAJOR}.{MINOR}.{PATCH}[-{PRERELEASE}]
```

**Components:**
- **SOLVEIT_VERSION**: SOLVE-IT knowledge base version (0.YYYY-MM format, matching upstream)
- **MAJOR**: Breaking changes to MCP server (0, 1, 2, ...)
- **MINOR**: New features, backward compatible (0, 1, 2, ...)
- **PATCH**: Bug fixes, security patches (0, 1, 2, ...)
- **PRERELEASE** (optional): Pre-release identifier (rc.1, beta.1, alpha.1)

### Examples

```
v0.2025-10-0.1.0        # SOLVE-IT 0.2025-10, MCP server v0.1.0
v0.2025-10-0.1.1        # SOLVE-IT 0.2025-10, MCP server v0.1.1 (patch)
v0.2025-10-0.2.0        # SOLVE-IT 0.2025-10, MCP server v0.2.0 (new feature)
v0.2025-11-0.2.0        # SOLVE-IT 0.2025-11, MCP server v0.2.0 (data update)
v0.2025-11-1.0.0        # SOLVE-IT 0.2025-11, MCP server v1.0.0 (major)
v0.2025-10-0.1.0-rc.1   # Release candidate 1
v0.2025-10-0.1.0-beta.1 # Beta release
```

## SOLVE-IT Version Detection

The GitHub Actions workflow automatically detects the SOLVE-IT version by:

1. Cloning the SOLVE-IT repository
2. Checking for a `VERSION` file
3. Falling back to git tags or commit date

**Manual Override:**
If auto-detection fails, the default version is `0.2025-10`. You can verify the detected version in the workflow logs.

## Creating a Release

### Prerequisites

- All tests passing on `main` branch
- No known security vulnerabilities
- Documentation updated
- CHANGELOG prepared

### Step-by-Step Process

#### 1. Determine Version Numbers

**Check current SOLVE-IT version:**
```bash
# Visit https://github.com/SOLVE-IT-DF/solve-it/releases
# Or check locally:
cd solve-it-main
git describe --tags --abbrev=0
```

**Determine MCP server version:**
- Current version: Check latest git tag
- Patch update (bug fix): Increment PATCH (0.1.0 → 0.1.1)
- Minor update (new feature): Increment MINOR (0.1.1 → 0.2.0)
- Major update (breaking change): Increment MAJOR (0.2.0 → 1.0.0)

**Construct full version:**
```
Format: v{SOLVEIT}-{MAJOR}.{MINOR}.{PATCH}
Example: v0.2025-10-0.1.0
```

#### 2. Update Local Repository

```bash
# Ensure clean state
cd ~/solve_it_mcp
git checkout main
git pull origin main
git status  # Should be clean
```

#### 3. Create Annotated Tag

```bash
# Create tag with detailed message
git tag -a v0.2025-10-0.1.0 -m "Release v0.2025-10-0.1.0

SOLVE-IT Knowledge Base: 0.2025-10
MCP Server Version: 0.1.0

Features:
- List new features
- List improvements
- List bug fixes

Changes in this release:
- Describe major changes
- Describe minor changes

Breaking Changes:
- List breaking changes (or 'None')

Security:
- All platforms scanned for CRITICAL/HIGH vulnerabilities
- No security issues detected

Dependencies:
- Python 3.12
- MCP SDK 1.0.0+
- OpenTelemetry 1.21.0+
"
```

#### 4. Push Tag to Trigger Workflow

```bash
git push origin v0.2025-10-0.1.0
```

#### 5. Monitor Build Process

**Go to:** https://github.com/3soos3/solve_it_mcp/actions

**Expected workflow execution:**

```
1. determine-strategy
   - Detects: full scan mode
   - Outputs: 3 platforms (amd64, arm64, arm/v7)
   - Detects SOLVE-IT version: 0.2025-10
   Duration: ~30 seconds

2. security-scan (matrix)
   - security-scan (linux/amd64)    ~5 minutes
   - security-scan (linux/arm64)   ~10 minutes  } Parallel
   - security-scan (linux/arm/v7)  ~12 minutes
   Duration: ~12 minutes (longest job)

3. build-and-push
   - Build multi-arch image         ~8 minutes
   - Run smoke tests                ~2 minutes
   - Push to Docker Hub             ~2 minutes
   - Create GitHub Release          ~10 seconds
   Duration: ~12 minutes

Total: ~24 minutes
```

#### 6. Verify Release

**Check Docker Hub:**
```bash
# Visit: https://hub.docker.com/r/3soos3/solve-it-mcp/tags

# Should see:
# - 3soos3/solve-it-mcp:v0.2025-10-0.1.0
# - 3soos3/solve-it-mcp:latest
# - 3soos3/solve-it-mcp:sha-abc1234
```

**Check GitHub Release:**
```bash
# Visit: https://github.com/3soos3/solve_it_mcp/releases

# Should see:
# - Auto-created release
# - Release notes populated
# - Docker pull commands
# - Security scan confirmation
```

**Verify Multi-Arch:**
```bash
docker manifest inspect 3soos3/solve-it-mcp:v0.2025-10-0.1.0

# Should show manifests for:
# - linux/amd64
# - linux/arm64
# - linux/arm/v7
```

**Test Image:**
```bash
# Pull and test
docker pull 3soos3/solve-it-mcp:v0.2025-10-0.1.0

# Run locally
docker run --rm -d -p 8000:8000 3soos3/solve-it-mcp:v0.2025-10-0.1.0

# Test health
curl http://localhost:8000/healthz

# Expected: {"status":"healthy","service":"solveit-mcp-server"}
```

## Pre-Release Process

For testing before official release:

### Release Candidate (RC)

```bash
# Create RC tag
git tag -a v0.2025-10-0.1.0-rc.1 -m "Release candidate 1 for v0.2025-10-0.1.0"
git push origin v0.2025-10-0.1.0-rc.1

# Workflow triggers:
# - Full scan (3 platforms)
# - Marked as pre-release in GitHub
# - Docker tags: v0.2025-10-0.1.0-rc.1

# Test in staging environment
# If issues found: v0.2025-10-0.1.0-rc.2
# Final release: v0.2025-10-0.1.0
```

### Beta Release

```bash
git tag -a v0.2025-10-0.2.0-beta.1 -m "Beta release for testing"
git push origin v0.2025-10-0.2.0-beta.1
```

### Alpha Release

```bash
git tag -a v0.2025-10-0.3.0-alpha.1 -m "Alpha release for early testing"
git push origin v0.2025-10-0.3.0-alpha.1
```

## Version Update Scenarios

### Scenario 1: Security Patch

```
Current: v0.2025-10-0.1.0
Fix: CVE in dependency
Next: v0.2025-10-0.1.1

Steps:
1. Fix vulnerability
2. Merge to main
3. git tag -a v0.2025-10-0.1.1 -m "Security patch: Update vulnerable dependency"
4. git push origin v0.2025-10-0.1.1
```

### Scenario 2: New Feature

```
Current: v0.2025-10-0.1.1
Feature: Add new MCP tool
Next: v0.2025-10-0.2.0

Steps:
1. Implement feature
2. Merge to main
3. git tag -a v0.2025-10-0.2.0 -m "Add new enhanced search tool"
4. git push origin v0.2025-10-0.2.0
```

### Scenario 3: SOLVE-IT Data Update

```
Current: v0.2025-10-0.2.0
Update: SOLVE-IT releases 0.2025-11
Next: v0.2025-11-0.2.0

Steps:
1. Verify SOLVE-IT 0.2025-11 compatibility
2. Update documentation if needed
3. git tag -a v0.2025-11-0.2.0 -m "Update to SOLVE-IT 0.2025-11 dataset"
4. git push origin v0.2025-11-0.2.0

Note: Data is fetched automatically during build
```

### Scenario 4: Breaking Change

```
Current: v0.2025-11-0.2.0
Change: Redesign MCP protocol
Next: v0.2025-11-1.0.0

Steps:
1. Implement breaking changes
2. Update documentation
3. git tag -a v0.2025-11-1.0.0 -m "Major release: Breaking API changes

BREAKING CHANGES:
- MCP endpoint structure changed
- Tool parameters restructured
- Client updates required
"
4. git push origin v0.2025-11-1.0.0
```

## Security Scanning

### Automatic Scanning

All releases (including pre-releases) trigger **full multi-platform scanning**:

- **Platforms scanned**: linux/amd64, linux/arm64, linux/arm/v7
- **Severity levels**: CRITICAL, HIGH
- **Exit behavior**: Build fails if vulnerabilities found
- **Reports**: SARIF files uploaded to GitHub Security tab

### Manual Security Review

Before each release:

1. **Check Security tab:**
   - https://github.com/3soos3/solve_it_mcp/security

2. **Review Dependabot alerts:**
   - https://github.com/3soos3/solve_it_mcp/security/dependabot

3. **Check base image:**
   - Verify `python:3.12-slim` has no known HIGH/CRITICAL CVEs

### If Security Issues Found

```bash
# Workflow will fail with exit code 1
# Check SARIF reports in Security tab
# Fix vulnerabilities
# Delete failed tag:
git tag -d v0.2025-10-0.1.0
git push origin :refs/tags/v0.2025-10-0.1.0

# Re-create tag after fixes
git tag -a v0.2025-10-0.1.0 -m "..."
git push origin v0.2025-10-0.1.0
```

## Rollback Process

If a release has critical issues:

### Option 1: Create Patch Release

```bash
# Fix issue
git checkout main
# ... make fixes ...
git commit -m "Fix critical issue in v0.2025-10-0.1.0"
git push origin main

# Create patch release
git tag -a v0.2025-10-0.1.1 -m "Hotfix for critical issue"
git push origin v0.2025-10-0.1.1
```

### Option 2: Delete Release (Not Recommended)

```bash
# Delete GitHub release (manual via UI)
# Delete Docker Hub tags (manual via UI)
# Delete git tag
git tag -d v0.2025-10-0.1.0
git push origin :refs/tags/v0.2025-10-0.1.0
```

## Helm Chart Updates

After Docker release, update Helm chart:

```bash
cd ~/solve-it-charts

# Update charts/solve-it-mcp/Chart.yaml
# appVersion: "v0.2025-10-0.1.0"

# Update charts/solve-it-mcp/values.yaml
# image.tag: "v0.2025-10-0.1.0"

git add charts/solve-it-mcp/
git commit -m "Update to SOLVE-IT MCP v0.2025-10-0.1.0"
git push origin main

# Create Helm chart release
git tag -a v0.1.1 -m "Helm chart v0.1.1 for SOLVE-IT MCP v0.2025-10-0.1.0"
git push origin v0.1.1
```

## Troubleshooting

### Build Fails on ARM Platforms

```bash
# Check workflow logs for platform-specific errors
# Common issues:
# - Missing ARM-compatible dependencies
# - QEMU emulation timeouts (increase timeout)
# - Platform-specific CVEs

# Test locally:
podman build --platform linux/arm64 -t test:arm64 .
podman build --platform linux/arm/v7 -t test:armv7 .
```

### Trivy Scan Fails

```bash
# View SARIF report in Security tab
# Identify vulnerable packages
# Update requirements.txt or base image
# Re-run build

# Bypass (NOT RECOMMENDED for production):
# Modify workflow: exit-code: '0'
```

### SOLVE-IT Version Detection Fails

```bash
# Check workflow logs for detection errors
# Manual override in tag message if needed
# Verify SOLVE-IT repository is accessible
```

### Docker Push Fails

```bash
# Check Docker Hub credentials
# Verify DOCKERHUB_USERNAME secret
# Verify DOCKERHUB_TOKEN secret
# Check Docker Hub rate limits
```

## Best Practices

1. **Always test in staging** before production release
2. **Use release candidates** for major versions
3. **Document breaking changes** clearly
4. **Update CHANGELOG** before tagging
5. **Verify all tests pass** on main before tagging
6. **Monitor security alerts** continuously
7. **Keep dependencies updated** regularly
8. **Test multi-arch images** on different platforms

## Related Documentation

- [Multi-Architecture Testing](../MULTIARCH_TESTING.md)
- [Docker Documentation](DOCKER.md)
- [Kubernetes Documentation](KUBERNETES.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

## Support

For release issues:
- **GitHub Issues**: https://github.com/3soos3/solve_it_mcp/issues
- **Email**: 3soos3@users.noreply.github.com
