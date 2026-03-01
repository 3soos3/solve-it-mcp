# SOLVE-IT MCP Server Documentation

Welcome to the comprehensive documentation for the **SOLVE-IT MCP Server** - a production-ready Model Context Protocol server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base.

## What is SOLVE-IT MCP Server?

SOLVE-IT MCP Server is a production-ready implementation that exposes the entire SOLVE-IT digital forensics knowledge base through 20+ specialized tools. It enables Large Language Models (LLMs) to assist with digital forensics investigations by providing programmatic access to:

- **Techniques** (T1001, T1002...): Digital forensic investigation methods
- **Weaknesses** (W1001, W1002...): Potential problems/limitations of techniques
- **Mitigations** (M1001, M1002...): Ways to address weaknesses
- **Objectives**: Categories that organize techniques by investigation goals

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

    Complete reference for all 20+ MCP tools

- :material-file-document: **[Techniques Reference](reference/techniques.md)**

    Understanding SOLVE-IT techniques

- :material-alert-circle: **[Weaknesses Reference](reference/weaknesses.md)**

    Technique weaknesses and limitations

- :material-shield-check: **[Mitigations Reference](reference/mitigations.md)**

    Addressing technique weaknesses

</div>

### Architecture & Development

<div class="grid cards" markdown>

- :material-sitemap: **[Architecture Overview](architecture/overview.md)**

    System design and components

- :material-security: **[Security Model](architecture/security-model.md)**

    Multi-layer security architecture

- :material-file-code: **[Implementation Details](architecture/implementation.md)**

    Technical implementation deep-dive

- :material-account-group: **[Contributing](development/contributing.md)**

    How to contribute to the project

</div>

## Key Features

- **🔒 Production-Ready Security**: Alpine Linux base with zero CVEs, comprehensive security scanning
- **🌐 Multi-Platform Support**: Native images for AMD64, ARM64, and ARMv7 (Raspberry Pi)
- **📊 OpenTelemetry Observability**: Built-in metrics, tracing, and logging
- **⚡ High Performance**: Optimized shared knowledge base, sub-second response times
- **🔄 Dual Transport Modes**: HTTP/SSE for Kubernetes, stdio for desktop clients
- **📦 Minimal Footprint**: 60MB Alpine-based image (highly optimized)
- **☸️ Kubernetes Native**: Production-grade Helm charts with health checks and auto-scaling

## About SOLVE-IT

SOLVE-IT (Standardized Framework for Investigation and Law Enforcement Operations in Technology) is a systematic digital forensics knowledge base inspired by MITRE ATT&CK. It provides comprehensive mappings of investigation techniques, their weaknesses, and mitigations.

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

See the [For Researchers](guides/for-researchers.md) guide for detailed citation information.

## Need Help?

- **Documentation Issues**: Check the [Troubleshooting Guide](guides/troubleshooting.md)
- **Bug Reports**: [Open an issue on GitHub](https://github.com/3soos3/solve-it-mcp/issues)
- **Security Vulnerabilities**: See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)
- **General Questions**: [Start a discussion](https://github.com/3soos3/solve-it-mcp/discussions)
