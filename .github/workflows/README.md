# GitHub Actions Workflows

This directory contains the CI/CD workflows for the SOLVE-IT MCP Server.

## Workflow Architecture

The workflows are organized by responsibility for fast feedback and clear separation of concerns:

### 1. **ci.yml** - Code Quality & Tests
- **Triggers:** PR + Main push
- **Duration:** ~3-5 minutes
- **Purpose:** Fast feedback on code quality
- **Jobs:**
  - Code quality (Ruff linting, format check)
  - Type checking (mypy)
  - Unit tests (pytest with coverage, Python 3.11 & 3.12)
  - YAML linting

### 2. **security.yml** - Vulnerability Scanning
- **Triggers:** PR + Main push + Daily schedule
- **Duration:** ~2-3 minutes  
- **Purpose:** Security vulnerability detection
- **Jobs:**
  - Python code security (Bandit)
  - Dependency vulnerabilities (pip-audit, Safety)
  - Dockerfile security (Hadolint)
  - Secret scanning (TruffleHog)

### 3. **docker-pr-validation.yml** - Docker Build Validation
- **Triggers:** PR only
- **Duration:** ~10-12 minutes
- **Purpose:** Validate Docker builds before merge
- **Jobs:**
  - Single-arch build (linux/amd64 for speed)
  - Health check tests (/healthz, /readyz)
  - Multi-arch build verification
  - Trivy security scan
- **Note:** Does NOT publish images

### 4. **docker-publish.yml** - Production Build & Publish
- **Triggers:** Main push + Git tags + Workflow call
- **Duration:** ~20 minutes
- **Purpose:** Build and publish production Docker images
- **Jobs:**
  - Verify CI passed
  - Multi-arch builds (amd64, arm64, arm/v7)
  - SBOM generation (SPDX, CycloneDX, Syft)
  - Image signing (Cosign keyless)
  - Push to Docker Hub
  - Security scan (Trivy on all platforms)
- **Security Features:**
  - SBOM attached to images
  - Images signed with Cosign
  - Provenance attestation
  - Complete audit trail

### 5. **docker-monthly.yml** - Smart Rebuild
- **Triggers:** Monthly schedule (1st of month)
- **Duration:** Variable (only runs if needed)
- **Purpose:** Rebuild images when SOLVE-IT updates
- **Logic:**
  - Check SOLVE-IT for new releases
  - Compare with last published version
  - Only trigger rebuild if SOLVE-IT updated
  - Calls docker-publish.yml workflow

## Workflow Execution Flow

### On Pull Request:
```
┌─────────────────────────────────────────────┐
│ PR Opened/Updated                           │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────┐           ┌──────────────┐
│ ci.yml   │           │ security.yml │
│ ~5 min   │           │ ~3 min       │
└─────┬────┘           └──────┬───────┘
      │                       │
      │    ┌──────────────────┘
      │    │
      ▼    ▼
┌────────────────────────┐
│ docker-pr-validation   │
│ ~12 min                │
│ (validates build)      │
└────────────────────────┘

Total: ~12 minutes (parallel execution)
```

### On Main Branch Merge:
```
┌─────────────────────────────────────────────┐
│ Merged to Main                              │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────┐           ┌──────────────┐
│ ci.yml   │           │ security.yml │
│ ~5 min   │           │ ~3 min       │
└─────┬────┘           └──────┬───────┘
      │                       │
      └──────────┬────────────┘
                 │ (both must pass)
                 ▼
      ┌────────────────────┐
      │ docker-publish.yml │
      │ ~20 min            │
      │ (multi-arch build) │
      │ (SBOM + sign)      │
      │ (publish)          │
      └────────────────────┘

Total: ~25 minutes (sequential with CI gates)
```

### Monthly Schedule:
```
┌─────────────────────────────────────────────┐
│ 1st of Month @ 3 AM UTC                     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
      ┌────────────────────────┐
      │ docker-monthly.yml     │
      │ Check SOLVE-IT version │
      └───────────┬────────────┘
                  │
          ┌───────┴───────┐
          │               │
          ▼               ▼
    [No Update]    [Update Found]
    (Skip)               │
                         ▼
              ┌────────────────────┐
              │ docker-publish.yml │
              │ (full rebuild)     │
              └────────────────────┘
```

## Branch Protection Requirements

Configure branch protection on `main` with:

### Required Status Checks:
1. ✅ **CI Summary** (from ci.yml)
2. ✅ **Security Summary** (from security.yml)  
3. ✅ **PR Validation Summary** (from docker-pr-validation.yml)

All three must pass before merge is allowed.

### Configuration:
```
Settings → Branches → Branch protection rules → main
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  Required checks:
    - ci-summary
    - security-summary
    - pr-summary
☑ Require pull request reviews before merging (optional)
☑ Include administrators (recommended)
```

## Forensic Software Features

### Image Provenance & Integrity:
- **SBOM:** Every image has attached Software Bill of Materials
  - Formats: SPDX, CycloneDX, Syft
  - Lists all dependencies and versions
  - Required for compliance and auditing

- **Image Signing:** All images signed with Cosign (keyless)
  - Signatures stored in Sigstore transparency log
  - Tied to GitHub identity
  - Verifiable by anyone

- **Provenance:** Build attestations included
  - Source commit
  - Build parameters
  - Build environment

### Verification:
```bash
# Verify image signature
cosign verify <image> \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# View SBOM
cosign download sbom <image>

# View provenance
cosign download attestation <image>
```

## Artifacts Generated

### Every PR:
- Test coverage reports
- Security scan results (Bandit, pip-audit, Safety, Trivy)
- Hadolint SARIF results

### Every Main Build:
- SBOM files (SPDX, CycloneDX, Syft)
- Trivy scan results (all platforms)
- Docker image tags (sha, latest, version)

## Maintenance

### Updating Workflows:
1. Test changes in a PR (workflows run automatically)
2. Review workflow execution and logs
3. Merge when all checks pass

### Debugging Failed Workflows:
1. Check workflow summary in PR
2. Review job logs in Actions tab
3. Download artifacts for detailed reports

### Monitoring:
- Security scans run daily (schedule in security.yml)
- Monthly rebuilds check for SOLVE-IT updates
- Dependabot monitors dependencies (if enabled)

## File Locations

- **Workflows:** `.github/workflows/`
- **Workflow Backup:** `.github/workflows/backup/`
- **Branch Protection Docs:** `docs/development/branch-protection.md`

## Migration Notes

Previous monolithic `ci.yml` and `docker-publish.yml` have been split for:
- ✅ Faster PR feedback (parallel execution)
- ✅ Clear separation of concerns
- ✅ Better forensic audit trail
- ✅ Easier maintenance and debugging

Old workflows backed up in `.github/workflows/backup/`.
