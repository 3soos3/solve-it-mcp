# Security Model

Multi-layer security architecture for SOLVE-IT MCP Server.

!!! note "Production Use Disclaimer"
    This is a best-effort maintained project. For critical forensic use, perform your own security audit.

## Security Layers

### 1. Container Security

**Base Image**: Python 3.12-Alpine

- Minimal attack surface (~5 MB base image)
- Zero CRITICAL/HIGH CVEs maintained via regular scanning and monthly rebuilds
- Multi-stage build: build tools (`git`, `cargo`, `rust`) are excluded from the runtime image

**Non-root user** (`mcpuser`, UID 1000):

```dockerfile
USER mcpuser
```

**Recommended runtime flags** in production:

```yaml
securityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop: ["ALL"]
```

### 2. Input Validation

All tool parameters are validated by Pydantic before execution:

- Type-safe parameter handling
- Auto-generated JSON schemas
- Input sanitization middleware
- Execution timeout per tool (45 s default)
- Input size limits

### 3. Network Security

**Rate limiting**: application-level per-client request limiting.

### 4. Authentication & Authorization

**Current state**: none (open access).

**Recommended for production**:

- API key authentication
- OAuth2/OIDC
- Kubernetes Network Policies
- Service mesh mTLS (Istio)

### 5. Cryptographic Verification (GHCR Only)

GHCR images are signed with Cosign keyless signing and include an SBOM and SLSA provenance attestation.

**Verify image authenticity:**

```bash
cosign verify ghcr.io/3soos3/solve-it-mcp:latest \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

**Download SBOM:**

```bash
cosign download sbom ghcr.io/3soos3/solve-it-mcp:latest
```

**View build provenance:**

```bash
cosign download attestation ghcr.io/3soos3/solve-it-mcp:latest | jq
```

### 6. Audit & Logging

- All requests logged with correlation IDs
- JSON structured logging for SIEM integration
- OpenTelemetry traces covering the complete request lifecycle

### 7. Automated Security Scanning

Every PR and main-branch push triggers:

- **Trivy** — container vulnerability scanning (blocks on CRITICAL/HIGH)
- **Bandit** — Python security linting
- **Safety / pip-audit** — dependency vulnerability databases
- **Hadolint** — Dockerfile best practices
- **TruffleHog / Gitleaks** — secret detection

Daily scheduled scans also run to catch newly published CVEs.

### 8. License Compliance

Automated checks block GPL/AGPL dependencies. Only MIT-compatible licenses are permitted.

---

## Threat Model

### In Scope

- Malicious or malformed input to MCP tools
- Resource exhaustion (CPU, memory)
- Unauthorized access in HTTP mode
- Information disclosure in error messages

### Out of Scope

- Physical access to the host
- Supply chain attacks (mitigated by SBOM verification)
- Social engineering

---

## Security Best Practices

### Production Deployment

1. Use GHCR images with signature verification
2. Verify SBOM before deployment
3. Run as non-root (default)
4. Use Kubernetes Network Policies
5. Enable audit logging (`LOG_FORMAT=json`)
6. Configure resource limits
7. Use TLS (via reverse proxy or service mesh)
8. Implement authentication (API keys or OAuth2)
9. Keep images updated (monthly rebuild workflow)

### Forensic Use (Chain of Custody)

1. Document the image SHA256 digest
2. Verify cryptographic signatures with Cosign
3. Store the SBOM alongside your evidence
4. Enable `FORENSIC_METADATA=true` to embed version and timestamp in every tool response
5. Log all tool invocations with correlation IDs
6. Run on an isolated network

---

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
- [Docker Deployment — Security](../deployment/docker.md#security)
- [Kubernetes Deployment](../deployment/kubernetes.md)
