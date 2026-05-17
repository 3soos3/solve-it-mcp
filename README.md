# SOLVE-IT MCP Server

[![Release](https://img.shields.io/github/v/release/3soos3/solve-it-mcp?sort=semver)](https://github.com/3soos3/solve-it-mcp/releases/latest)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://3soos3.github.io/solve-it-mcp/)
[![CI - Code Quality](https://github.com/3soos3/solve-it-mcp/workflows/CI%20-%20Code%20Quality%20%26%20Tests/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/ci.yml)
[![Security Scanning](https://github.com/3soos3/solve-it-mcp/workflows/Security%20-%20Vulnerability%20Scanning/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/security.yml)
[![License Compliance](https://github.com/3soos3/solve-it-mcp/workflows/License%20Compliance/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/license-compliance.yml)
[![OpenSSF Scorecard](https://github.com/3soos3/solve-it-mcp/workflows/OpenSSF%20Scorecard/badge.svg)](https://github.com/3soos3/solve-it-mcp/security/code-scanning)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/3soos3/solve-it-mcp/graphs/commit-activity)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/3soos3/solve-it-mcp)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![Docker Image Size](https://img.shields.io/docker/image-size/3soos3/solve-it-mcp/latest)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production-ready MCP server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base.**

SOLVE-IT is a systematic digital forensics knowledge base inspired by MITRE ATT&CK. This MCP server exposes the entire SOLVE-IT knowledge base through **24 tools** that enable LLMs to assist with digital forensics investigations.

## Documentation

**[View Complete Documentation →](https://3soos3.github.io/solve-it-mcp/)**

- **Getting Started**: [5-Minute Quick Start](https://3soos3.github.io/solve-it-mcp/getting-started/)
- **For Forensic Analysts**: [Practical Investigation Guide](https://3soos3.github.io/solve-it-mcp/guides/for-forensic-analysts/)
- **For Researchers**: [Citation & Academic Use](https://3soos3.github.io/solve-it-mcp/guides/for-researchers/)
- **Deployment**: [Docker](https://3soos3.github.io/solve-it-mcp/deployment/docker/) | [Kubernetes](https://3soos3.github.io/solve-it-mcp/deployment/kubernetes/)
- **Troubleshooting**: [Common Issues & Solutions](https://3soos3.github.io/solve-it-mcp/guides/troubleshooting/)

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker pull 3soos3/solve-it-mcp:latest
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest

curl http://localhost:8000/healthz
```

[Complete Docker Guide →](https://3soos3.github.io/solve-it-mcp/deployment/docker/)

### Option 2: Desktop MCP Client (Claude Desktop, Cline, etc.)

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

### Option 3: Python

```bash
git clone https://github.com/3soos3/solve-it-mcp.git
cd solve-it-mcp
pip install -e .
SOLVE_IT_DATA_PATH=/path/to/solve-it/data python3 src/server.py
```

[Local Development Guide →](https://3soos3.github.io/solve-it-mcp/development/local-testing/)

## Key Features

- **Production-Ready Security**: Alpine Linux base, zero CVEs, comprehensive security scanning
- **Multi-Platform Support**: Native images for `linux/amd64`, `linux/arm64`, `linux/arm/v7`
- **OpenTelemetry Observability**: Built-in metrics, tracing, and structured logging
- **High Performance**: Shared knowledge base singleton — ~1 second startup, sub-second queries
- **Dual Transport**: `http` for Kubernetes; `stdio` for Claude Desktop and local tools
- **Minimal Footprint**: ~60 MB Alpine-based image
- **Kubernetes Native**: Production-grade Helm charts with health checks and HPA

## What is SOLVE-IT?

SOLVE-IT provides structured digital forensics knowledge through:

- **Techniques** (DFT-XXXX) — digital forensic investigation methods
- **Weaknesses** (DFW-XXXX) — potential problems or limitations of techniques
- **Mitigations** (DFM-XXXX) — ways to address weaknesses
- **Citations** (DFCite-XXXX) — academic and industry references
- **Objectives** — investigation workflow phases grouping techniques

**Learn more**: [SOLVE-IT-DF/solve-it](https://github.com/SOLVE-IT-DF/solve-it)

## Available Tools (24)

| Category | Tools |
|---|---|
| Core Information | `get_database_description`, `search` |
| Detailed Lookup | `get_technique_details`, `get_weakness_details`, `get_mitigation_details` |
| Relationship Analysis | `get_weaknesses_for_technique`, `get_mitigations_for_weakness`, `get_techniques_for_weakness`, `get_weaknesses_for_mitigation`, `get_techniques_for_mitigation`, `get_mitigations_for_technique`, `get_objectives_for_technique` |
| Objective Management | `list_objectives`, `get_techniques_for_objective`, `list_available_mappings`, `load_objective_mapping` |
| Citations | `get_citation`, `resolve_inline_citations` |
| Bulk Retrieval | `get_all_techniques_with_name_and_id`, `get_all_weaknesses_with_name_and_id`, `get_all_mitigations_with_name_and_id`, `get_all_techniques_with_full_detail`, `get_all_weaknesses_with_full_detail`, `get_all_mitigations_with_full_detail` |

[Complete Tools Reference →](https://3soos3.github.io/solve-it-mcp/reference/tools-overview/)

## Security & Verification

- **Vulnerability Scanning**: Trivy, Bandit, Safety, pip-audit
- **SBOM**: Software Bill of Materials (GHCR images)
- **Image Signing**: Cryptographic signatures via Cosign (GHCR images)
- **License Compliance**: Automated dependency checking
- **OpenSSF Scorecard**: Public security rating

### Forensic Verification (GHCR Images)

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

Docker Hub images do **not** include Cosign signatures/SBOM. Use GHCR for forensic compliance.

[Security Policy →](SECURITY.md)

## Citation

```bibtex
@software{solve_it_mcp,
  author = {3soos3},
  title = {SOLVE-IT MCP Server},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/3soos3/solve-it-mcp}
}
```

[Complete Citation Guide →](https://3soos3.github.io/solve-it-mcp/guides/for-researchers/)

## Contributing

Contributions are welcome. See:

- [Development Setup](https://3soos3.github.io/solve-it-mcp/development/local-testing/)
- [Testing Guide](https://3soos3.github.io/solve-it-mcp/development/testing-guide/)

## License & Attribution

Licensed under the MIT License. See [LICENSE](LICENSE).

This is a fork and significant enhancement of the original [solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) by CKE-Proto, with additions including production Docker deployment, multi-architecture support, security scanning, OpenTelemetry observability, Kubernetes deployment, and comprehensive documentation.

**Original Project**: [CKE-Proto/solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) (MIT License)

## Links

- **Documentation**: https://3soos3.github.io/solve-it-mcp/
- **GitHub**: https://github.com/3soos3/solve-it-mcp
- **Docker Hub**: https://hub.docker.com/r/3soos3/solve-it-mcp
- **GHCR**: https://github.com/3soos3/solve-it-mcp/pkgs/container/solve-it-mcp
- **Issues**: https://github.com/3soos3/solve-it-mcp/issues
- **SOLVE-IT Framework**: https://github.com/SOLVE-IT-DF/solve-it
