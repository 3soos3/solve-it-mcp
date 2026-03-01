# SOLVE-IT MCP Server

[![Release](https://img.shields.io/github/v/release/3soos3/solve-it-mcp?sort=semver)](https://github.com/3soos3/solve-it-mcp/releases/latest)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://3soos3.github.io/solve-it-mcp/)
[![CI - Code Quality](https://github.com/3soos3/solve-it-mcp/workflows/CI%20-%20Code%20Quality%20%26%20Tests/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/ci.yml)
[![Security Scanning](https://github.com/3soos3/solve-it-mcp/workflows/Security%20-%20Vulnerability%20Scanning/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/security.yml)
[![License Compliance](https://github.com/3soos3/solve-it-mcp/workflows/License%20Compliance/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/license-compliance.yml)
[![OpenSSF Scorecard](https://github.com/3soos3/solve-it-mcp/workflows/OpenSSF%20Scorecard/badge.svg)](https://github.com/3soos3/solve-it-mcp/security/code-scanning)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/3soos3/solve-it-mcp/graphs/commit-activity)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/3soos3/solve-it-mcp)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![Docker Image Size](https://img.shields.io/docker/image-size/3soos3/solve-it-mcp/latest)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production-ready MCP server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base.**

SOLVE-IT is a systematic digital forensics knowledge base inspired by MITRE ATT&CK, containing comprehensive mappings of investigation techniques, weaknesses, and mitigations. This MCP server exposes the entire SOLVE-IT knowledge base through 20+ tools that enable LLMs to assist with digital forensics investigations.

## 📚 Documentation

**[View Complete Documentation →](https://3soos3.github.io/solve-it-mcp/)**

### Quick Links

- **Getting Started**: [5-Minute Quick Start](https://3soos3.github.io/solve-it-mcp/getting-started/)
- **For Forensic Analysts**: [Practical Investigation Guide](https://3soos3.github.io/solve-it-mcp/guides/for-forensic-analysts/)
- **For Researchers**: [Citation & Academic Use](https://3soos3.github.io/solve-it-mcp/guides/for-researchers/)
- **Deployment**: [Docker](https://3soos3.github.io/solve-it-mcp/deployment/docker/) | [Kubernetes](https://3soos3.github.io/solve-it-mcp/deployment/kubernetes/)
- **Troubleshooting**: [Common Issues & Solutions](https://3soos3.github.io/solve-it-mcp/guides/troubleshooting/)

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Pull and run
docker pull 3soos3/solve-it-mcp:latest
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e HTTP_PORT=8000 \
  3soos3/solve-it-mcp:latest

# Test it
curl http://localhost:8000/healthz
```

[Complete Docker Guide →](https://3soos3.github.io/solve-it-mcp/deployment/docker/)

### Option 2: Desktop MCP Client (Claude Desktop, etc.)

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "solveit": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio",
               "3soos3/solve-it-mcp:latest"]
    }
  }
}
```

[Integration Guide →](https://3soos3.github.io/solve-it-mcp/guides/integration/)

### Option 3: Python Installation

```bash
git clone https://github.com/3soos3/solve-it-mcp.git
cd solve-it-mcp
pip install -r requirements.txt
python3 src/server.py
```

[Local Development Guide →](https://3soos3.github.io/solve-it-mcp/development/local-testing/)

## ✨ Key Features

- **🔒 Production-Ready Security**: Alpine Linux base with zero CVEs, comprehensive security scanning
- **🌐 Multi-Platform Support**: Native images for AMD64, ARM64, and ARMv7 (Raspberry Pi)
- **📊 OpenTelemetry Observability**: Built-in metrics, tracing, and logging
- **⚡ High Performance**: Optimized shared knowledge base, sub-second response times
- **🔄 Dual Transport Modes**: HTTP/SSE for Kubernetes, stdio for desktop clients
- **📦 Minimal Footprint**: 60MB Alpine-based image (highly optimized)
- **☸️ Kubernetes Native**: Production-grade Helm charts with health checks and auto-scaling

## 🔍 What is SOLVE-IT?

SOLVE-IT provides a structured approach to digital forensics investigations through:

- **Techniques** (T1001, T1002...): Digital forensic investigation methods
- **Weaknesses** (W1001, W1002...): Potential problems/limitations of techniques  
- **Mitigations** (M1001, M1002...): Ways to address weaknesses
- **Objectives**: Categories that organize techniques by investigation goals

**Learn more**: [SOLVE-IT-DF/solve-it](https://github.com/SOLVE-IT-DF/solve-it)

## 🛠️ Available Tools (20+)

The server provides comprehensive tools organized into categories:

- **Core Information**: Database description, search across all types
- **Detailed Lookup**: Get specific technique, weakness, or mitigation details
- **Relationship Analysis**: Explore connections between techniques, weaknesses, and mitigations
- **Objective Management**: Work with investigation objectives and mappings
- **Bulk Operations**: Retrieve complete datasets for analysis

[Complete Tools Reference →](https://3soos3.github.io/solve-it-mcp/reference/tools-overview/)

## 🔒 Security & Verification

### Automated Security

- ✅ **Vulnerability Scanning**: Trivy, Bandit, Safety, pip-audit
- ✅ **SBOM**: Software Bill of Materials (GHCR images)
- ✅ **Image Signing**: Cryptographic signatures via Cosign (GHCR images)
- ✅ **License Compliance**: Automated dependency checking
- ✅ **OpenSSF Scorecard**: Public security rating

### Forensic Verification (GHCR Images)

For organizations requiring cryptographic verification:

```bash
# Verify image signature
cosign verify ghcr.io/3soos3/solve-it-mcp:latest \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# Download SBOM
cosign download sbom ghcr.io/3soos3/solve-it-mcp:latest | jq

# View build provenance
cosign download attestation ghcr.io/3soos3/solve-it-mcp:latest | jq
```

**Note**: Docker Hub images do NOT include Cosign signatures/SBOM to keep tags clean. Use GHCR for forensic compliance.

[Security Policy →](SECURITY.md) | [Architecture Details →](https://3soos3.github.io/solve-it-mcp/architecture/implementation/)

## 📖 Citation

If you use this software in forensic investigations or research, please cite it:

```bibtex
@software{solve_it_mcp,
  author = {3soos3},
  title = {SOLVE-IT MCP Server},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/3soos3/solve-it-mcp}
}
```

[Complete Citation Guide for Researchers →](https://3soos3.github.io/solve-it-mcp/guides/for-researchers/)

## 🤝 Contributing

Contributions are welcome! Please see:

- [Contributing Guide](https://3soos3.github.io/solve-it-mcp/development/contributing/) (coming soon)
- [Development Setup](https://3soos3.github.io/solve-it-mcp/development/local-testing/)
- [Testing Guide](https://3soos3.github.io/solve-it-mcp/development/testing-guide/)

## 📄 License & Attribution

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Attribution

This is a fork and significant enhancement of the original [solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) by CKE-Proto.

**Major Enhancements**:
- Production-ready Docker deployment with multi-architecture support
- Comprehensive security scanning and SBOM generation
- OpenTelemetry observability integration
- Kubernetes-native deployment with Helm charts
- Complete documentation restructure with MkDocs Material
- Enhanced testing and CI/CD pipelines

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.

**Original Project**: [CKE-Proto/solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) (MIT License)

## 🔗 Links

- **Documentation**: https://3soos3.github.io/solve-it-mcp/
- **GitHub Repository**: https://github.com/3soos3/solve-it-mcp
- **Docker Hub**: https://hub.docker.com/r/3soos3/solve-it-mcp
- **GitHub Container Registry**: https://github.com/3soos3/solve-it-mcp/pkgs/container/solve-it-mcp
- **Issue Tracker**: https://github.com/3soos3/solve-it-mcp/issues
- **Security Policy**: [SECURITY.md](SECURITY.md)
- **SOLVE-IT Framework**: https://github.com/SOLVE-IT-DF/solve-it

## 💬 Support

- **Documentation**: [Complete Documentation](https://3soos3.github.io/solve-it-mcp/)
- **Troubleshooting**: [Common Issues](https://3soos3.github.io/solve-it-mcp/guides/troubleshooting/)
- **Bug Reports**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- **Security Issues**: See [SECURITY.md](SECURITY.md)

---

**For complete documentation, deployment guides, and detailed usage examples, visit:**  
**https://3soos3.github.io/solve-it-mcp/**
