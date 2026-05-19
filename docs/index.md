# SOLVE-IT MCP Server

**Production-ready MCP server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base.**

SOLVE-IT MCP Server exposes the SOLVE-IT knowledge base through 24 specialized tools, enabling LLMs to assist with digital forensics investigations by providing structured access to:

- **Techniques** (DFT-XXXX) — digital forensic investigation methods
- **Weaknesses** (DFW-XXXX) — potential problems or limitations of techniques
- **Mitigations** (DFM-XXXX) — ways to address weaknesses
- **Citations** (DFCite-XXXX) — academic and industry references
- **Objectives** — investigation workflow phases that group techniques

## Quick Navigation

### Getting Started

<div class="grid cards" markdown>

- :material-rocket-launch: **[Quick Start Guide](getting-started.md)**

    Get up and running in 5 minutes with Docker or Python

- :material-microscope: **[For Forensic Analysts](guides/for-forensic-analysts.md)**

    Practical guide for digital forensics professionals

- :material-school: **[For Researchers](guides/for-researchers.md)**

    Academic usage, citation, and reproducibility guidelines

- :material-puzzle: **[Troubleshooting](guides/troubleshooting.md)**

    Common issues and solutions

</div>

### Deployment

<div class="grid cards" markdown>

- :material-docker: **[Docker Deployment](deployment/docker.md)**

    Complete guide for Docker-based deployments

- :material-kubernetes: **[Kubernetes Deployment](deployment/kubernetes.md)**

    Production Kubernetes setup with Helm charts

</div>

### Reference Documentation

<div class="grid cards" markdown>

- :material-tools: **[Tools Overview](reference/tools-overview.md)**

    Complete reference for all 24 MCP tools

- :material-variable: **[Environment Variables](reference/environment-variables.md)**

    All configuration options explained

</div>

### Architecture & Development

<div class="grid cards" markdown>

- :material-sitemap: **[Architecture Overview](architecture/overview.md)**

    System design and components

- :material-security: **[Security Model](architecture/security-model.md)**

    Multi-layer security architecture

- :material-file-code: **[Implementation Details](architecture/implementation.md)**

    CI/CD and release pipeline overview

- :material-test-tube: **[Testing Guide](development/testing-guide.md)**

    Local and multi-arch testing

</div>

## Key Features

- **Production-Ready Security**: Alpine Linux base, zero CVEs, comprehensive security scanning
- **Multi-Platform Support**: Native images for `linux/amd64`, `linux/arm64`, `linux/arm/v7`
- **OpenTelemetry Observability**: Built-in metrics, tracing, and structured logging
- **High Performance**: Shared knowledge base singleton — ~1 second startup, sub-second queries
- **Dual Transport**: `http` for Kubernetes and web clients; `stdio` for Claude Desktop and local tools
- **Minimal Footprint**: ~60 MB Alpine-based image
- **Kubernetes Native**: Production-grade Helm charts with health checks and HPA

## About SOLVE-IT

SOLVE-IT is a systematic digital forensics knowledge base inspired by MITRE ATT&CK. It provides structured mappings of investigation techniques, their weaknesses, and mitigations.

**Learn more**: [SOLVE-IT-DF/solve-it on GitHub](https://github.com/SOLVE-IT-DF/solve-it)

## Project Links

- **GitHub Repository**: [3soos3/solve-it-mcp](https://github.com/3soos3/solve-it-mcp)
- **Docker Hub**: [3soos3/solve-it-mcp](https://hub.docker.com/r/3soos3/solve-it-mcp)
- **GitHub Container Registry**: [ghcr.io/3soos3/solve-it-mcp](https://github.com/3soos3/solve-it-mcp/pkgs/container/solve-it-mcp)
- **Security Policy**: [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)
- **Issue Tracker**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)

## License & Citation

This project is licensed under the MIT License. If you use this software in forensic investigations or research, please cite it:

```bibtex
@software{solve_it_mcp,
  author = {3soos3},
  title = {SOLVE-IT MCP Server},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/3soos3/solve-it-mcp}
}
```

See the [For Researchers](guides/for-researchers.md) guide for full citation guidance.

## Need Help?

- **Documentation Issues**: Check the [Troubleshooting Guide](guides/troubleshooting.md)
- **Bug Reports**: [Open an issue on GitHub](https://github.com/3soos3/solve-it-mcp/issues)
- **Security Vulnerabilities**: See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)
- **General Questions**: [Start a discussion](https://github.com/3soos3/solve-it-mcp/discussions)
