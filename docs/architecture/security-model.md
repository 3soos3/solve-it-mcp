# Security Model

Multi-layer security architecture for SOLVE-IT MCP Server.

!!! info "Production Use Disclaimer"
    This is a best-effort maintained project. For critical forensic use, perform your own security audit and consider maintaining your own fork.

## Security Layers

### 1. Container Security

**Base Image**: Alpine Linux 3.23
- Minimal attack surface (5MB base image)
- Zero CRITICAL/HIGH vulnerabilities
- Regular security updates

**Non-Root User**:
```dockerfile
USER mcpuser:1000
```

**Read-Only Filesystem** (recommended in production):
```yaml
securityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### 2. Network Security

**CORS Configuration**:
- Configurable allowed origins
- Credential handling controls
- Method restrictions

**Rate Limiting** (application level):
- Per-client request limits
- Configurable thresholds
- Protection against DoS

### 3. Input Validation

**Pydantic-based Validation**:
- All tool parameters validated
- Type-safe parameter handling
- Auto-generated JSON schemas

**Security Middleware**:
- Request sanitization
- Input size limits
- Malicious pattern detection

### 4. Authentication & Authorization

**Current State**: None (open access)

**Recommended for Production**:
- Add API key authentication
- Implement OAuth2/OIDC
- Use service mesh (Istio) for mTLS
- Network policies in Kubernetes

### 5. Cryptographic Verification

**Docker Image Signing** (GHCR only):
```bash
# Verify image authenticity
cosign verify ghcr.io/3soos3/solve-it-mcp:latest \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

**SBOM Available**:
```bash
# Download Software Bill of Materials
cosign download sbom ghcr.io/3soos3/solve-it-mcp:latest
```

### 6. Audit & Logging

**Structured Logging**:
- All requests logged with correlation IDs
- Configurable log levels
- JSON format for SIEM integration

**OpenTelemetry Traces**:
- Complete request lifecycle tracking
- Performance monitoring
- Error tracking

### 7. Automated Security Scanning

**CI/CD Security**:
- ✅ Trivy (container vulnerability scanning)
- ✅ Bandit (Python security linter)
- ✅ Safety (dependency vulnerability DB)
- ✅ pip-audit (PyPI vulnerability DB)
- ✅ Hadolint (Dockerfile best practices)
- ✅ TruffleHog (secret detection)
- ✅ Gitleaks (secret scanning)

**Regular Scans**:
- Every PR
- Every main push
- Daily scheduled scans
- Monthly rebuilds

### 8. License Compliance

**Automated Checks**:
- Blocks GPL/AGPL dependencies
- Generates NOTICE file
- MIT-compatible only

## Threat Model

### In Scope

**Local Execution Risks**:
- Malicious input to tools
- Resource exhaustion
- Information disclosure

**Network Risks** (HTTP mode):
- Unauthorized access
- Data interception
- DoS attacks

### Out of Scope

- Physical access to host
- Supply chain attacks (use SBOM for verification)
- Social engineering

## Security Best Practices

### For Production Deployment

1. **Use GHCR images** with signature verification
2. **Verify SBOM** before deployment
3. **Run as non-root** (default)
4. **Use network policies** (Kubernetes)
5. **Enable audit logging**
6. **Configure resource limits**
7. **Use TLS** for HTTP transport
8. **Implement authentication**
9. **Regular updates** (monthly rebuild workflow)
10. **Monitor with SIEM**

### For Forensic Use

**Chain of Custody**:
- Document image SHA256
- Verify cryptographic signatures
- Maintain SBOM records
- Log all tool invocations

**Evidence Integrity**:
- Run on isolated networks
- Use read-only mode when possible
- Audit all queries
- Maintain correlation IDs

## Vulnerability Reporting

See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md) for:
- Reporting process
- Response expectations
- Supported versions

## Security Resources

- [OpenSSF Scorecard](https://github.com/3soos3/solve-it-mcp/security/code-scanning)
- [Security Advisories](https://github.com/3soos3/solve-it-mcp/security/advisories)
- [Dependency Graph](https://github.com/3soos3/solve-it-mcp/network/dependencies)

## Related Documentation

- [Architecture Overview](overview.md)
- [Implementation Details](implementation.md)
- [Docker Security](../deployment/docker.md#security)
- [Kubernetes Security](../deployment/kubernetes.md#security)
