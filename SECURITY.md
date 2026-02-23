# Security Policy

## ⚠️ Project Status

This is an **open-source project maintained on a best-effort basis**. 

**Important Limitations:**
- No guaranteed response time for security issues
- No SLA for fixes
- Security patches provided when time permits
- Use at your own risk in production environments

## Reporting a Vulnerability

If you discover a security vulnerability:

### GitHub Security Advisories (Preferred)
1. Go to: https://github.com/3soos3/solve-it-mcp/security/advisories/new
2. Click "Report a vulnerability"
3. Provide details

**OR**

### Public Issue
For non-sensitive issues, you may open a public GitHub issue.

## Response Expectations

- **Acknowledgment**: Best effort, no guaranteed timeline
- **Fixes**: Provided when maintainer availability permits
- **Disclosure**: Public vulnerabilities may be disclosed immediately if no fix is planned

## Security Features

This project includes automated security scanning:

- ✅ **Dependency Scanning**: Trivy, Safety, pip-audit
- ✅ **Code Security**: Bandit (Python security linter)
- ✅ **Container Security**: Trivy image scanning
- ✅ **Dockerfile Linting**: Hadolint
- ✅ **License Compliance**: Automated license checking
- ✅ **Dependabot**: Automated dependency updates
- ✅ **OpenSSF Scorecard**: Public security rating

## Use in Production

**For production/forensic use:**
- Perform your own security audit
- Review all dependencies
- Consider forking and maintaining your own version
- Verify SBOM and signatures on Docker images

## Supported Versions

| Version | Status |
| ------- | ------ |
| latest  | Best effort support |
| < latest| No support |

---

**This project is provided "AS IS" without warranty. See [LICENSE](LICENSE) for details.**
